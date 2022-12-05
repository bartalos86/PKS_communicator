import server
import client


def start():
    exit = False
    show_menu = True
    switch_data = None
    while not exit:
        if show_menu:
            print("What functionality do you want:")
            print("1 - server")
            print("2 - client")
            print("3 - exit")
            option = int(input())

        if option == 1:
            print("Starting server...")
            if switch_data != None:
                print(switch_data)
                switch_data = server.start(server_p_address=switch_data["destination_addr"])
            else:
                switch_data = server.start()
            print(switch_data)
            if switch_data != None:
                option = 2
                show_menu = False
            else:
                show_menu = True
                exit = True
           
        elif option == 2:
            print("Starting client...")
            if switch_data != None:
                switch_data = client.start(destination_p_address=switch_data["server_address"])
            else:
                switch_data = client.start()
            print(switch_data)

            if switch_data != None:
                option = 1
                show_menu = False
            else:
                show_menu = True
                exit = True

        elif option == 3:
            exit = True
        else:
            print("Unknown command")
        

start()
