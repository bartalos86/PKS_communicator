import server
import client


def start():
    exit = False
    while not exit:
        print("What functionality do you want:")
        print("1 - server")
        print("2 - client")
        print("3 - exit")
        option = int(input())

        if option == 1:
            print("Starting server...")
            server.start()
        elif option == 2:
            print("Starting client...")
            client.start()
        elif option == 3:
            exit = True
        else:
            print("Unknown command")
        

start()
