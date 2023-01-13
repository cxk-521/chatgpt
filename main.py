from flask import Flask, request
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy import parse_message
from wechatpy.replies import TextReply
import eventlet
import requests

app = Flask(__name__)

TOKEN = "12345678"

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer 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'
}

class User:#定义这个类使得每个用户的缓冲不冲突
    currentMSG=""#当前post
    lastMSG=""#上一次post的结果
    userSource=""#区别每个用户的唯一ID
    def __init__(self,currentmsg,lastmsg,usersource):
        self.currentMSG=currentmsg
        self.lastMSG=lastmsg
        self.userSource=usersource

Users=[]
UserSources=[]
t=0
# def swap():
#     global currentMSG
#     global lastMSG
#     currentMSG=""
#     t=currentMSG
#     currentMSG=lastMSG
#     lastMSG=t
# def getSTR(s2):
#     global lastMSG
#     lastMSG=s2
def swap(user1):#将上一次的结果保留在这一次中替换

    t=user1.currentMSG
    user1.currentMSG=user1.lastMSG
    user1.lastMSG=t

@app.route("/", methods=["GET", "POST"])
def index():
    times=0
    if (request.method == "GET"):
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echostr = request.args.get('echostr')
        token = TOKEN
        try:
            check_signature(token, signature, timestamp, nonce)
        except InvalidSignatureException:
            # 处理异常情况或忽略
            return "校验失败"
        # 校验成功
        return echostr
    if (request.method == "POST"):
        xml_str = request.data
        # 解析xml格式数据
        msg = parse_message(xml_str)
        xml_str = request.data
        # 解析xml格式数据
        msg = parse_message(xml_str)
        # 1.目标用户信息
        target = msg.target
        # 2.发送用户信息
        source = msg.source
        # 3.消息类型
        msgType = msg.type
        # 4.消息内容
        msgCcontent = msg.content


        print(msgCcontent)

        reply = TextReply()
        reply.source = target
        reply.target = source
        # answer = chat.ask(msgCcontent)[0]

        json_data = {
            'model': 'text-davinci-003',
            'prompt': msgCcontent,
            'max_tokens': 4000,
            'temperature': 0
        }

        eventlet.monkey_patch()
        time_limit=2
        # with eventlet.Timeout(time_limit, False):
        response = requests.post('https://api.openai.com/v1/completions', headers=headers, json=json_data)#post请求
        print("失败")
        print("成功")
        ss=response.json()['choices'][0]['text'].strip()
        if(ss==""):return reply.render("回复过长，请一段时间后输入‘你好’获取本次结果")
        if (len(ss) > 40):#因为openai反应比较慢，微信重传三次没有得到结果就会报错，重传三次的时间差不多就是40字符
            user = User("", ss, source)
            if(source not in UserSources):
                UserSources.append(source)
                Users.append(user)
            else:
                for user in Users:
                    if(source==user.userSource):
                        user.lastMSG=ss


        global t
        t+=1
        reply.content=ss
        for user in Users:
            if source==user.userSource:
                # print(user.userSource+user.lastMSG+user.currentMSG)
                if(len(user.currentMSG)!=0):
                    reply.content+="\n上一句的回复：\n"+user.currentMSG
                    if(t>=4):#重传三次加上下一次响应获得上一次的结果一共四次
                        user.lastMSG=""
                        user.currentMSG=""
                        t=0
                # elif(len(user.lastMSG)!=0):
                #     reply.content+="\n上一句的回复：\n"+user.lastMSG
                #     if(t==3):
                #         user.lastMSG=""
                swap(user)



        print(reply.content)
        # 包装成XML格式的数据
        xml = reply.render()
        return xml



if __name__ == '__main__':
    app.run(port=80)