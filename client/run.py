from player import Player
import argparse

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--server-url", type=str, help="server urls or ip")
    parser.add_argument("-p", "--port", type=int, help="server port")

    args = parser.parse_args()

    # create player instance and run the player
    player = Player(serlver_url=args.server_url, port=args.port)
    player.run()


if __name__ == "__main__":
    main()