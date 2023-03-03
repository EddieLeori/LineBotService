from lib.utility import *
from app import LineBotService

if __name__ == "__main__":
    linebot = LineBotService()
    linebot.run()
    Log("LineBotService close.")
    