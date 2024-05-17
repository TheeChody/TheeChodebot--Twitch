"""
This ain't in use...
Just kept thee code incase I give this another try
"""

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("600x420")
        self.title("TheeChodebot -- Twitch")
        self.resizable(False, False)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)  #, uniform="z")

        Test(self)

    def options_menu(self):
        option_window = customtkinter.CTkToplevel(self)
        option_window.title(f"TheeChodebot -- Twitch -- Options Menu")
        option_window.geometry("420x420")
        option_window.resizable(False, False)

        title_line = customtkinter.CTkLabel(option_window, text=f"Options Menu")
        title_line.grid(row=0, column=1, padx=10, pady=10)

        client_id_label = customtkinter.CTkLabel(option_window, text=f"Twitch Client ID")
        client_id_label.grid(row=1, column=0, padx=10, pady=10)

        client_id = customtkinter.StringVar()
        client_id_box = customtkinter.CTkEntry(option_window, textvariable=client_id)
        client_id_box.grid(row=1, column=2, padx=10, pady=10)
        # OptionsMenu(self)

    # @staticmethod async def run():
    #     twitch_helper = UserAuthenticationStorageHelper(twitch_bot, target_scopes)
    #     await twitch_helper.bind()
    #
    #     user = await first(twitch_bot.get_users())
    #
    #     event_sub = EventSubWebsocket(twitch_bot)
    #     event_sub.start()
    #
    #     # await event_sub.listen_extension_bits_transaction_create()
    #     await event_sub.listen_stream_online(id_theechody_account, on_stream_start)
    #     await event_sub.listen_channel_ad_break_begin(id_theechody_account, on_stream_ad_start)
    #     await event_sub.listen_channel_follow_v2(id_theechody_account, user.id, on_stream_follow)
    #     await event_sub.listen_channel_chat_message(id_theechody_account, user.id, on_stream_message)
    #     await event_sub.listen_channel_points_custom_reward_redemption_add(id_theechody_account,
    #                                                                        on_stream_channel_point_redemption)
    #     await event_sub.listen_channel_poll_begin(id_theechody_account, on_stream_poll_start)
    #     await event_sub.listen_channel_poll_end(id_theechody_account, on_stream_poll_end)
    #     await event_sub.listen_channel_subscribe(id_theechody_account, on_stream_subbie)
    #     await event_sub.listen_channel_subscription_gift(id_theechody_account, on_stream_subbie_gift)
    #     await event_sub.listen_channel_cheer(id_theechody_account, on_stream_cheer)
    #     await event_sub.listen_channel_raid(on_stream_raid_in, to_broadcaster_user_id=id_theechody_account)
    #     await event_sub.listen_channel_raid(on_stream_raid_out, from_broadcaster_user_id=id_theechody_account)
    #     await event_sub.listen_stream_offline(id_theechody_account, on_stream_end)
    #
    #     while True:
    #         async def shutdown():
    #             try:
    #                 print("Shutting down processes. Stand By")
    #                 await event_sub.stop()
    #                 await twitch_bot.close()
    #                 await disconnect_mongo()
    #                 print("Processes shut down successfully")
    #             except Exception as e:
    #                 print(f"Error in shutdown() -- {e}")
    #                 pass
    #
    #         try:
    #             user_input = input("Enter 1 to Start Timer\nEnter 2 to Stop Timer\nEnter 0 to Exit Program\n")
    #             if user_input.isdigit():
    #                 user_input = int(user_input)
    #             if user_input in (1, 2):
    #                 print("Values 1 & 2 Not Programmed Yet")
    #             elif user_input == 0:
    #                 await shutdown()
    #                 break
    #             else:
    #                 print(f"{user_input} is not valid")
    #         except Exception as e:
    #             if KeyboardInterrupt:
    #                 await shutdown()
    #                 break
    #             else:
    #                 print(f"Error in while loop -- {e}")
    #                 pass


class Test(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.pack(pady=20)

        self.title_line = customtkinter.CTkLabel(self, text=f"Welcome to TheeChodebot's Twitch Interface")
        self.title_line.grid(row=0, column=1, padx=10, pady=10)

        self.test_button = customtkinter.CTkButton(self, text="Click", command=parent.options_menu)
        self.test_button.grid(row=1, column=0, padx=10, pady=10)

        # self.test_button2 = customtkinter.CTkButton(self, text="Click 2", command=lambda: threading.Thread(target=asyncio.run(run())).start())
        self.test_button2 = customtkinter.CTkButton(self, text="Click 2", command=lambda: threading.Thread(target=self.run_twitch_bot()).start())
        # self.test_button2 = customtkinter.CTkButton(self, text="Click 2", command=lambda: asyncio.run(run()))
        self.test_button2.grid(row=1, column=1, padx=10, pady=10)

        self.test_button3 = customtkinter.CTkButton(self, text="Click 3")
        self.test_button3.grid(row=1, column=2, padx=10, pady=10)

    @staticmethod
    def run_twitch_bot():
        asyncio.run(run())


app = App()
app.mainloop()
