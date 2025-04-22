# -*- coding: utf-8 -*-

import sys
import qi
import argparse
import time


def main(session):
    # 获取服务
    motion_service = session.service("ALMotion")
    posture_service = session.service("ALRobotPosture")
    tts_service = session.service("ALTextToSpeech")

    # 1. 唤醒机器人
    motion_service.wakeUp()

    # 2. 切换到Stand姿势
    posture_service.goToPosture("Stand", 1.0)

    # 3. 让Nao说话
    tts_service.say("Hello, I am going to wave my hand. Watch me!")

    # 4. 让Nao挥右手
    #   - 首先保证右手关节可动
    motion_service.setStiffnesses("RArm", 1.0)

    #   - 设置关节名称和目标角度（弧度制）
    #     shoulderPitch:  肩部前后摆动（0 ~ +正值抬臂前）
    #     shoulderRoll :  肩部左右摆动（正值往外打开手臂）
    #     elbowYaw    :   肘部旋转
    #     elbowRoll   :   肘关节弯曲(负值向内弯, 正值向外弯)
    #     wristYaw    :   手腕旋转
    #     hand        :   手掌张开/闭合（0关，1开）

    #   - 先抬起手
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll"]
    angles = [0.0, -0.5, 1.5, 1.0]  # 举个示例角度
    fractionMaxSpeed = 0.2  # 移动速度
    motion_service.setAngles(names, angles, fractionMaxSpeed)

    time.sleep(1.0)

    #   - 让手臂来回摆动几次
    for i in range(3):
        # 向外摆
        motion_service.setAngles("RElbowRoll", 0.5, 0.2)
        time.sleep(0.5)
        # 向内摆
        motion_service.setAngles("RElbowRoll", 1.0, 0.2)
        time.sleep(0.5)

    # 5. 说话并将手放回初始
    tts_service.say("That is me waving my hand. Thank you for watching!")

    # 让手恢复到一个相对自然的姿势
    angles = [1.5, 0.0, 1.0, 0.5]
    motion_service.setAngles(names, angles, fractionMaxSpeed)

    # 如果需要把机器人恢复坐姿并关节下电，可执行下面两行
    # posture_service.goToPosture("Sit", 1.0)
    # motion_service.rest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="192.168.1.35",
                        help="Nao机器人IP地址")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi端口号，默认为9559")
    args = parser.parse_args()

    # 建立与Naoqi会话
    connection_url = "tcp://" + args.ip + ":" + str(args.port)
    app = qi.Application(["NaoMotionTest", "--qi-url=" + connection_url])
    app.start()

    session = app.session
    main(session)