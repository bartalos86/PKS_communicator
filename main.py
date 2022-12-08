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
            try:
                option = int(input("Your choice: "))
            except:
                print("Value is not a correct number")
                continue

        if option == 1:
            print("Starting server...")
            if switch_data != None:
                switch_data = server.start(server_p_address=switch_data["own_address"])
            else:
                switch_data = server.start()
            if switch_data != None:
                option = 2
                show_menu = False
            else:
                show_menu = True
                exit = True
           
        elif option == 2:
            print("Starting client...")
            if switch_data != None:
                switch_data = client.start(destination_p_address=switch_data["client_address"])
            else:
                switch_data = client.start()

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
