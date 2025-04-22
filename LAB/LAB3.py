from naoqi import ALProxy
import time


def main(robotIP="192.168.1.35", port=9559):

    trackerProxy = ALProxy("ALTracker", robotIP, port)

    trackerProxy.registerTarget("Face", 0.1)
    trackerProxy.setMode("Head")
    trackerProxy.track("Face")

    print("NAO is tracking a face.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")

    trackerProxy.stopTracker()
    trackerProxy.unregisterAllTargets()


if __name__ == "__main__":
    NAO_IP = "192.168.1.35"
    NAO_PORT = 9559
    main(NAO_IP, NAO_PORT)