from flask import Flask, request, abort
from lib.utility import *
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

import os
import json
import ssl

class LineBotService:
    def __init__(self):
        self.name = 'LineBotService'
        self.sertkey = ""
        self.sertpem = ""
        self.host = '0.0.0.0'
        self.port = 5123
        self.botid = None
        self.secret = None
        self.token = None
        self.is_tag_reply = "0" # 是否tag才回話.1:是
        self.is_init = False

        self.call_fun_join = None
        self.call_fun_enter = None
        self.call_fun_leave = None
        self.call_fun_message = None
        self.call_fun_postback = None

        self.init()

        self.app = Flask(__name__)
        self.app.add_url_rule("/check", methods=['POST'], view_func= self.check) 
        self.app.add_url_rule("/callback", methods=['POST'], view_func= self.callback)

    def init(self):
        try:
            with open('option.json', 'r') as f:
                cfg = json.load(f)
                f.close()
                Log(cfg)
                if self.name not in cfg:
                    return
                if "sertpem" in cfg[self.name]:
                    self.sertpem = cfg[self.name]["sertpem"]
                if "sertkey" in cfg[self.name]:
                    self.sertkey = cfg[self.name]["sertkey"]
                if "host" in cfg[self.name]:
                    self.host = cfg[self.name]["host"]
                if "port" in cfg[self.name]:
                    self.port = cfg[self.name]["port"]
                if "botid" in cfg[self.name]:
                    self.botid = cfg[self.name]["botid"]
                if "secret" in cfg[self.name]:
                    self.secret = cfg[self.name]["secret"]
                if "token" in cfg[self.name]:
                    self.token = cfg[self.name]["token"]
                if "is_tag_reply" in cfg[self.name]:
                    self.is_tag_reply = cfg[self.name]["is_tag_reply"]

                self.line_bot_api = LineBotApi(self.token)
                self.handler = WebhookHandler(self.secret)
                # 把對應的line事件註冊處理
                # 新用戶加入群組觸發
                @self.handler.add(MemberJoinedEvent)
                def handel_joined(event):
                    uid = event.joined.members[0].user_id
                    gid = event.source.group_id
                    profile = self.line_bot_api.get_group_member_profile(gid, uid)
                    name = profile.display_name
                    Log("MemberJoinedEvent={0},{1},{2}".format(uid, gid, name))
                    # do reply
                    self.join(event.reply_token, uid, gid, name)

                # 用戶退出群組觸發
                @self.handler.add(LeaveEvent)
                def handle_leave(event):
                    Log("LeaveEvent")

                # 進出事件
                @self.handler.add(BeaconEvent)
                def handle_beacon(event):
                    hwid = event.beacon.hwid
                    beacon_type = event.beacon.type
                    Log("BeaconEvent={0},{2}".format(hwid, beacon_type))
                    if beacon_type == "enter":
                        # do reply
                        self.enter(event.replay_token)
                    elif beacon_type == "leave":
                        # do reply
                        self.leave(event.replay_token)

                # 用戶傳送訊息
                @self.handler.add(MessageEvent, message=TextMessage)
                def handle_message(event):
                    msg = event.message.text
                    Log("MessageEvent={0},{1}".format(event.reply_token, msg))
                    # do reply
                    self.message(event.reply_token, msg)

                # 添加Bot好友觸發
                @self.handler.add(FollowEvent)
                def handle_follw(event):
                    Log("FollowEvent")
                
                # 取消添加Bot好友觸發
                @self.handler.add(UnfollowEvent)
                def handle_unfollw(event):
                    Log("UnfollowEvent")

                # 用戶回覆Bot
                @self.handler.add(PostbackEvent)
                def handle_message(event):
                    data = event.postback.data
                    Log("PostbackEvent={0}".format(data))
                    # do reply
                    self.postback(event.reply_token, data)

                # init ok here
                self.is_init = True
                Log("{0} init ok.".format(self.name))
        except:
            Log(self.name + " init eror!")
            return False
        return True
    
    def run(self):
        if self.is_init == True:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.load_cert_chain(self.sertpem, self.sertkey)
            self.app.run(self.host, self.port, ssl_context = context)

    def check(self):
        text = 'check ok!'
        Log(text)
        return text
    
    def callback(self):
        # get X-Line-Signature header value
        signature = request.headers['X-Line-Signature']
        # get request body as text
        body = request.get_data(as_text=True)
        Log("callback={0}".format(body))
        # self.app.logger.info("Request body: " + body)
        # handle webhook body
        try:
            self.handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
        return 'OK'
        
    def replayMessage(self, token, msg):
        self.line_bot_api.reply_message(token, msg)
        Log("reply={0},{1}".format(token, msg))

    def join(self, token, uid, gid, name):
        if self.call_fun_join is not None:
            self.call_fun_join(token, name)
        else:
            message = TextSendMessage(text=f'{name}歡迎加入')
            self.replayMessage(token, message)

    def enter(self, token):
        if self.call_fun_enter is not None:
            self.call_fun_enter(token)
        else:
            message = TextSendMessage(text='歡迎您！')
            self.replayMessage(token, message)
    
    def leave(self, token):
        if self.call_fun_leave is not None:
            self.call_fun_leave(token)
        else:
            message = TextSendMessage(text='感謝您！')
            self.replayMessage(token, message)

    def message(self, token, msg):
        # 判斷是否全部都回還是被tag才回
        if (self.is_tag_reply == "1" and \
            "@" + self.botid in msg or \
                "#" + self.botid in msg) or \
            (self.is_tag_reply == "0"):
            if self.call_fun_message is not None:
                self.call_fun_message(token, msg)
            else:
                message = TextSendMessage(text=msg)
                self.replayMessage(token, message)
        
    def postback(self, token, data):
        if self.call_fun_postback is not None:
            self.call_fun_postback(token, data)
        else:
            if data == 'action1':
                message = TextSendMessage(text='您点击了第一个按钮！')
            elif data == 'action2':
                message = TextSendMessage(text='您点击了第二个按钮！')
            self.replayMessage(token, message)

