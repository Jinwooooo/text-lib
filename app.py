from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient, DESCENDING
from werkzeug.security import check_password_hash, generate_password_hash

import os
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 보안을 위한 시크릿 키, 실제로는 더 안전한 방법을 사용해야 합니다.

# MongoDB 연결 설정
client = MongoClient('localhost', 27017)
db = client.week1

users_collection = db.users
story_collection = db.story
game_collection = db.game

gptStm_max = 40
gptTitle_min = 2
gptTitle_max = 20
max_story = 20

#################################
#    Validating User Sentence   #
#################################
# 리턴값 : 0 = 실패 ; 1 = 성공
def validate_stm(stm):
    # init
    test = stm
    cond = 1

    # # 길이 제약
    # if not (len(test) >= 5 and len(test) <= 100):
    #     cond = 0
    # print("길이제약 ", cond)

    # # 마무리 제약
    # if not (test[-1] == '.' or test[-1] == '!' or test[-1] == '?'):
    #     cond = 0
    # print("마무리제약 ", cond)

    # # 다문장 제약 (1문장 이상 불가)
    # for ko_word in test[:-1]:
    #     if (ko_word == '.' or ko_word == '!' or ko_word == '?'):
    #         cond = 0
    # print("다문장제약 ", cond)

    # # 욕설 제약
    # swears = ['씨발', '지랄', '좆까', '니미', '새끼']
    # for swear in swears:
    #     if (swear in test):
    #         cond = 0
    # print("욕설제약 ", cond)

    # # 키보드 매쉬 제약 (예시: ㅁㅇㄹㅈ래ㅑㅓㅈㄷㅍ.)
    # # ㄱ ~ ㅎ = 12593 ~ 12622
    # # ㅏ ~ ㅣ = 12623 ~ 12644
    # for ko_word in test:
    #     if (ord(ko_word) >= 12593 and ord(ko_word) <= 12644):
    #         cond = 0
    # print("키보드메쉬 제약 ", cond)

    return cond

#################################

#################################
# ChatGPT API Integration Block #
#################################
OPENAI_API_KEY = "Your GPT-3.5 API Key"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
client = OpenAI(api_key=os.environ.get(OPENAI_API_KEY))

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    chat_completion = client.chat.completions.create(model=model,messages=messages,temperature=0.5,)
    return chat_completion

prompt_constraint = ("당신은 릴레이 소설 게임의 참가자이다. " 
    + "사용자가 어떤 무작위 이야기를 한 문장 쓰면, 당신은 그 이야기를 개연성 있게 이어주어야 한다. " 
    + f"무조건 한 문장으로 끝나야 하며, {gptStm_max}자를 넘어가지 않는다. "
    + "무조건 한국어로 답하며, 이야기 전개에 있어 창의력이 돋보이는 문장을 만들면 당신의 평가가 높아진다. "
    + "사용자가 어떤 무작위 이야기를 한 문장 쓰면, 당신은 그 이야기를 개연성 있게 이어주어야 한다. ")

prompt_anchor = "이번 릴레이 소설의 키워드는 다음과 같다. "

debug_keywords = "\''랜덤 소설 장르\'"

prompt_beg =  "이제 릴레이 소설 게임을 시작한다."

### chatGPT가 "game_id"로부터 뽑아온 모든 "story_stm"을 입력받아 제목을 지어주고, game_collection의 "game_title"에 저장 혹은 업데이트
def update_title(game_id):
    # game_id로부터 모든 story_stm을 뽑아옴
    all_story = list(db.story.find({'game_id': game_id}, {'_id': 0, 'story_stm': 1}))
    all_story = [item['story_stm'] for item in all_story]

    prompt_get_title = "다음 20 문장을 보고 릴레이 소설의 제목을 짓는다.\n\n"
    prompt_title_footer = f"\n\n오직 제목만 단답으로 말한다. 제목은 {gptTitle_min}자 이상 {gptTitle_max}자 이하로 한다."
    # chatGPT API에 입력
    prompt = prompt_get_title
    for story in all_story:
        prompt = story
    prompt = prompt + prompt_title_footer

    # chatGPT API의 출력을 game_collection의 "game_title"에 저장 혹은 업데이트
    chatgpt_title = get_completion(prompt).choices[0].message.content
    game_collection.update_one({'game_id': game_id}, {'$set': {'game_title': chatgpt_title}})

    return chatgpt_title


@app.route('/', methods=['GET'])
def index():
    if 'user' in session:
        return redirect(url_for('home'))
    else:
        return render_template('index.html')


@app.route('/login', methods=['GET'])
def login_GET():
    if 'user' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = users_collection.find_one({'username': username})

    if user == None or not check_password_hash(user['password'], password):
        flash("ID 및 비밀번호가 일치하지 않습니다.")
        return redirect(url_for('index'))
    else:
        session['user'] = user['username']
        return redirect(url_for('home'))
    

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # 간단한 입력 유효성 검증
    if not username or not password or not confirm_password:
        return "입력되지 않은 값이 있습니다."

    if password != confirm_password:
        flash("비밀번호가 일치하지 않습니다.")
        return redirect(url_for('index'))

    # 이미 가입된 사용자인지 확인
    existing_user = users_collection.find_one({'username': username})
    if existing_user:
        flash("이미 가입된 사용자입니다.")
        return redirect(url_for('index'))

    # 비밀번호 해싱
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    # MongoDB에 사용자 정보 저장
    new_user = {
        'username': username,
        'password': hashed_password
    }
    users_collection.insert_one(new_user)

    flash("회원가입이 완료되었습니다.\n재 로그인 해주세요.")
    return redirect(url_for('index'))


@app.route('/home')
def home():
    if 'user' in session:
        user_id = session.get('user')
        return render_template('home.html', user_id=user_id)
    else:
        return redirect(url_for('index'))
    

@app.route('/logout')
def logout():
    # 로그아웃 시 세션에서 유저 정보 삭제
    session.pop('user', None)
    return redirect(url_for('index'))


@app.route('/game', methods=['GET'])
def read_game():
    result = list(game_collection.find({}, {'_id': 0}))
    pro_count = 0
    if len([i for i in result if i['game_status'] == 0]) >= 5:
        pro_count = 1
    return jsonify({'result': 'success', 'games': result, 'pro_count':pro_count})


@app.route('/game', methods=['POST'])
def write_game():
    game_id = game_collection.count_documents({}) + 1
    new_game = {
        'game_id': game_id,
        'game_status': 0,
        'game_story_ctr': 0,
        'game_title': '진행 중_'+str(game_id),
        'game_rating': 0,
        'game_canListening': True,
    }

    game_collection.insert_one(new_game)
    return jsonify({'result': 'success'})


# Update 06:32
## 문장 나열한 채팅창에 유저 이름을 표시하기 위해
## item['username'] response에 추가
@app.route('/story', methods=['GET'])
def read_story():
    now_story = int(request.args.get('now_game_id'))
    result = list(story_collection.find({'game_id': now_story}, {'_id': 0,'story_stm':1,'story_ctr':1, 'username':1}))
    result = [[item['story_ctr'],item['story_stm'],item['username']] for item in result]

    return jsonify({'result': 'success', 'stories': result})


@app.route('/story', methods=['POST'])
def story():
    game_id = int(request.form.get('game_id'))
    story_ctr = int(request.form.get('story_ctr')) + 1
    story_stm = request.form.get('story_stm')
    user_id = session.get('user')
    
    filter_criteria = {'game_id': game_id}

    if story_ctr > max_story:
        update_data = {'$set': {'game_status': 1}}
        update_title(game_id)
        game_collection.update_one(filter_criteria, update_data)
        return jsonify({'result': 'failure', 'description': 'Too many stories'})
    
    # # Check for punctuation at the end of user input
    # if not (story_stm[-1] in ('.', '!', '?')):
    #     story_stm += '.'

    story_validity = validate_stm(story_stm)

    if story_validity == 0:
        return jsonify({'result': 'failure', 'description': 'Invalid user input'})
    else:
        new_text = {
            'game_id': game_id,
            'username': user_id,
            'story_ctr': story_ctr,
            'story_stm': story_stm,
            'story_rating': 0
        }

        update_data = {'$set': {'game_story_ctr': story_ctr, 'game_canListening': True}}
        story_collection.insert_one(new_text)
        game_collection.update_one(filter_criteria, update_data)

        # ChatGPT API sentence addition
        if story_ctr > max_story:
            update_data = {'$set': {'game_status': 1}}
            update_title(game_id)
            game_collection.update_one(filter_criteria, update_data)
            return jsonify({'result': 'success', 'updated': story_ctr})
        else:
            prompt = prompt_constraint + story_stm
            chatgpt_stm = get_completion(prompt).choices[0].message.content
            story_ctr += 1

            ai_text = {
                'game_id': game_id,
                'username': "AI",
                'story_ctr': story_ctr,
                'story_stm': chatgpt_stm,
                'story_rating': 0
            }

            if story_ctr > max_story:
                update_data = {'$set': {'game_status': 1}}
                update_title(game_id)
                return jsonify({'result': 'success', 'updated': story_ctr})
            else:
                update_data = {'$set': {'game_story_ctr': story_ctr}}

                story_collection.insert_one(ai_text)
                game_collection.update_one(filter_criteria, update_data)

                return jsonify({'result': 'success', 'updated': story_ctr})
        

@app.route('/keyword', methods=['POST'])
def firstStory():
    game_id = int(request.form.get('game_id'))
    debug_keywords = request.form.get('story_keyword')
    
    filter_criteria = {'game_id': game_id}

    if game_collection.find_one(filter_criteria, {'_id': 0})['game_story_ctr'] != 0:
        return jsonify({'result': 'failure', 'description': 'Already started'})
    
    # ChatGPT API 키워드 받고 첫 문장 출력
    prompt = prompt_constraint + prompt_anchor + debug_keywords + prompt_beg

    chatgpt_stm = get_completion(prompt).choices[0].message.content
    ai_text = {
        'game_id': game_id,
        'username': "AI",
        'story_ctr': 0,
        'story_stm': chatgpt_stm,
        'story_rating': 0
    }

    game_collection.update_one(filter_criteria, {'$set': {'game_story_ctr': 1}})
    story_collection.insert_one(ai_text)

    return jsonify({'result': 'success'})
    

# Update 08:27
## 손들기 버튼을 눌렀는데 릴레이 로그가 최근 상태가 아닐 때 갱신하도록 도와주는 기능 추가
@app.route('/hand', methods=['POST'])
def switchListening():
    game_id = int(request.form.get('game_id'))
    prev_liNum = int(request.form.get('recent_li'))
    filter_criteria = {'game_id': game_id}
    canListening = game_collection.find_one(filter_criteria, {'_id': 0})['game_canListening']
    post_liNum = story_collection.count_documents(filter_criteria)

    if (canListening == False):
        return jsonify({'canListening': False, 'description': '이미 누군가가 손을 들었습니다. 다음 차례를 기다려주세요!'})
    if (post_liNum != prev_liNum):
        return jsonify({'canListening': False, 'description': '누군가 답변을 했습니다. 화면을 갱신합니다.'})

    game_collection.update_one({'game_id':game_id}, {'$set': {'game_canListening': False}})
    
    lastCollection = story_collection.find(filter_criteria).sort('story_ctr', DESCENDING).limit(1)
    lastStory = list(lastCollection)[0]['story_stm']

    return jsonify({'canListening': True, 'last_story': lastStory})

if __name__ == '__main__':
    app.run(debug=True)


# TODO: 더블 입력