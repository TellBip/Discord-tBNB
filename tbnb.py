import curl_cffi.requests
import json
import random
import time

standard_headers = {
    "Origin": "https://discord.com",
    "Referer": "https://discord.com/channels/@me",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Debug-Options": "bugReporterEnabled",
    "X-Discord-Locale": "en",
    "X-Discord-Timezone": "Etc/GMT-2",
}

def test_proxy(proxy):
    test_url = "https://httpbingo.org/ip"
    proxies = {
        "http": proxy,
        "https": proxy,
    } if proxy else None
    headers = standard_headers.copy()
    try:
        res = curl_cffi.requests.get(test_url, proxies=proxies, verify=False, headers=headers, impersonate="chrome136")
        if res.status_code == 200:
            return True
        else:
            print(f"Failed to connect using proxy: {res.status_code}")
            return False
    except curl_cffi.requests.RequestsError as e:
        print(f"Proxy test failed: {e}")
        return False

def get_context(wallet_address, command_name):
    return f"/{command_name} {wallet_address}"

def send_message(channel_id, authorization, proxy, content, command_name=None):
    if proxy and not test_proxy(proxy):
        print(f"Skipping message for wallet {wallet_address} due to proxy failure.")
        return False
    header = standard_headers.copy()
    header.update({
        "Authorization": authorization,
        "Content-Type": "application/json",
    })
    nonce = str(random.randint(10**15, 10**18))
    payload = {
        "mobile_network_type": "unknown",
        "content": content,
        "nonce": nonce,
        "tts": False,
        "flags": 0
    }
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy,
        }
    try:
        res = curl_cffi.requests.post(url=url, headers=header, json=payload, proxies=proxies, verify=False, impersonate="chrome136")
        if res.status_code == 200:
            print(f"Message sent to channel {channel_id} successfully.")
            return True
        else:
            print(f"Failed to send message: {res.status_code}, {res.content}")
            return False
    except curl_cffi.requests.RequestsError as e:
        print(f"Request error while sending message: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error while sending message: {e}")
        return False

def load_credentials(auth_file, proxy_file):
    auth_data = []
    proxy_data = []
    with open(auth_file, 'r') as f:
        for line in f.readlines():
            auth_info = line.strip().split('|')
            if len(auth_info) == 2:
                token = auth_info[0]
                command_and_wallet = auth_info[1].strip()
                if command_and_wallet.startswith('/'):
                    parts = command_and_wallet.split()
                    command_name = parts[0][1:] if len(parts) > 0 else "faucet"
                    wallet_address = parts[1] if len(parts) > 1 else ""
                else:
                    command_name = "faucet"
                    wallet_address = command_and_wallet
                auth_data.append({
                    'auth': token,
                    'command_name': command_name,
                    'wallet_address': wallet_address
                })
            elif len(auth_info) == 1 and auth_info[0]:
                # Если только токен, команда и кошелек не указаны
                token = auth_info[0]
                command_name = "faucet"
                wallet_address = ""
                auth_data.append({
                    'auth': token,
                    'command_name': command_name,
                    'wallet_address': wallet_address
                })
    if proxy_file:
        with open(proxy_file, 'r') as f:
            for line in f.readlines():
                proxy_data.append(line.strip())
    return auth_data, proxy_data

def get_recent_messages(channel_id, authorization, proxy, limit=2):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = standard_headers.copy()
    headers.update({
        "Authorization": authorization,
    })
    proxies = {
        "http": proxy,
        "https": proxy,
    } if proxy else None
    try:
        resp = curl_cffi.requests.get(url, headers=headers, proxies=proxies, verify=False, params={'limit': limit}, impersonate="chrome136")
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"Failed to fetch messages: {resp.status_code}, {resp.content}")
            return []
    except curl_cffi.requests.RequestsError as e:
        print(f"Request error while fetching messages: {e}")
        return []

def get_current_user_id(authorization, proxy):
    url = "https://discord.com/api/v9/users/@me"
    headers = standard_headers.copy()
    headers.update({
        "Authorization": authorization,
    })
    proxies = {
        "http": proxy,
        "https": proxy,
    } if proxy else None
    try:
        resp = curl_cffi.requests.get(url, headers=headers, proxies=proxies, verify=False, impersonate="chrome136")
        if resp.status_code == 200:
            user_data = resp.json()
            return user_data.get('id')
        else:
            print(f"Failed to fetch user data: {resp.status_code}, {resp.content}")
            return None
    except curl_cffi.requests.RequestsError as e:
        print(f"Request error while fetching user data: {e}")
        return None

def check_channel_membership(channel_id, authorization, proxy):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = standard_headers.copy()
    headers.update({
        "Authorization": authorization,
    })
    proxies = {
        "http": proxy,
        "https": proxy,
    } if proxy else None
    print(f"Checking channel membership for channel ID: {channel_id}...")
    try:
        resp = curl_cffi.requests.get(url, headers=headers, proxies=proxies, verify=False, params={'limit': 1}, impersonate="chrome136")
        if resp.status_code == 200:
            print(f"Successfully checked channel membership for channel {channel_id}. User is likely a member.")
            return True
        elif resp.status_code == 403:
             print(f"Channel membership check failed with 403 Forbidden for channel {channel_id}. Checking response content for error code...")
             return False
        else:
            print(f"Channel membership check returned unexpected status code {resp.status_code} for channel {channel_id}. Content: {resp.content}")
            return False
    except curl_cffi.requests.RequestsError as e:
        print(f"Request error while checking channel membership for channel {channel_id}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error while checking channel membership for channel {channel_id}: {e}")
        return False

def find_captcha_message(messages, current_user_id):
    for msg in messages:
        if msg['author']['id'] != current_user_id and msg.get('attachments'):
            for attachment in msg['attachments']:
                if 'content_type' in attachment and attachment['content_type'].startswith('image/'):
                    return attachment['url'], msg['id']
    return None, None

def create_dm_channel(authorization, proxy, bot_user_id):
    url = "https://discord.com/api/v9/users/@me/channels"
    headers = standard_headers.copy()
    headers.update({
        "Authorization": authorization,
        "Content-Type": "application/json",
    })
    payload = {"recipients": [bot_user_id]}
    proxies = {
        "http": proxy,
        "https": proxy,
    } if proxy else None
    try:
        resp = curl_cffi.requests.post(url, headers=headers, json=payload, proxies=proxies, verify=False, impersonate="chrome136")
        if resp.status_code == 200:
            channel_data = resp.json()
            channel_id = channel_data.get('id')
            print(f"Successfully created/obtained DM channel with bot {bot_user_id}. Channel ID: {channel_id}")
            return channel_id
        else:
            print(f"Failed to create/obtain DM channel with bot {bot_user_id}: {resp.status_code}, {resp.content}")
            return None
    except curl_cffi.requests.RequestsError as e:
        print(f"Request error while creating DM channel with bot {bot_user_id}: {e}")
        return None

def chat(auth_data, proxy_data):
    while True:
        padded_proxy_data = proxy_data + [None] * (len(auth_data) - len(proxy_data))
        for idx, (auth_info, proxy) in enumerate(zip(auth_data, padded_proxy_data)):
            authorization = auth_info['auth']
            wallet_address = auth_info['wallet_address']
            command_name = auth_info.get('command_name', 'faucet')
            current_user_id = get_current_user_id(authorization, proxy)
            if not current_user_id:
                print(f"Error: Failed to get user ID for account with wallet {wallet_address}. Skipping this account.")
                continue
            print(f"Processing account with user ID: {current_user_id} and wallet: {wallet_address}")
            target_server_channel_id = "1101022526550847508"
            account_line = f"{authorization}|/{command_name} {wallet_address}"
            if not check_channel_membership(target_server_channel_id, authorization, proxy):
                print(f"Account {current_user_id} failed channel membership check (or guild join attempt). Skipping this account.")
                print("Please ensure the user token is valid and the user can join the specified guild/channel.")
                with open("bad.txt", "a", encoding="utf-8") as fbad:
                    fbad.write(account_line + "\n")
                continue
            print(f"Channel membership check passed for account {current_user_id}. Proceeding.")
            bot_user_id = "1235890375151849485"
            print(f"Creating/obtaining DM channel with bot {bot_user_id} for account {current_user_id}.")
            dm_channel_id = create_dm_channel(authorization, proxy, bot_user_id)
            if not dm_channel_id:
                print(f"Error: Failed to create or obtain DM channel with bot {bot_user_id} for account {current_user_id}. Skipping this account.")
                continue
            print(f"Successfully obtained DM channel ID: {dm_channel_id} for account {current_user_id}.")
            content = get_context(wallet_address, command_name)
            send_success = send_message(dm_channel_id, authorization, proxy, content, command_name)
            if not send_success:
                print(f"Account {current_user_id}: Failed to send message. Saving to bad.txt and skipping.")
                with open("bad.txt", "a", encoding="utf-8") as fbad:
                    fbad.write(account_line + "\n")
                continue
            else:
                print(f"Account {current_user_id}: Message sent successfully. Saving to good.txt.")
                with open("good.txt", "a", encoding="utf-8") as fgood:
                    fgood.write(account_line + "\n")
            print("Waiting for bot response...")
            time.sleep(5)
            messages = get_recent_messages(dm_channel_id, authorization, proxy, limit=2)
            captcha_image_url, captcha_message_id = find_captcha_message(messages, current_user_id)
            if captcha_image_url:
                print("Captcha image found. Extracting solution from URL...")
                try:
                    filename = captcha_image_url.split('/')[-1]
                    captcha_solution = filename.split('?')[0].split('#')[0].rsplit('.', 1)[0]
                    if captcha_solution:
                        print(f"Extracted captcha solution: '{captcha_solution}'")
                        send_message(dm_channel_id, authorization, proxy, captcha_solution, command_name=None)
                        print("Waiting briefly for success message...")
                        time.sleep(3)
                        recent_messages_after_solution = get_recent_messages(dm_channel_id, authorization, proxy, limit=2)
                        success_message_found = False
                        if recent_messages_after_solution:
                            for msg_after in recent_messages_after_solution:
                                if msg_after['author']['id'] != current_user_id and "Success: Request created." in msg_after.get('content', ''):
                                    print("Success message 'Success: Request created.' found!")
                                    success_message_found = True
                                    break
                        if not success_message_found:
                            print("Success message 'Success: Request created.' not found in recent messages after sending solution.")
                    else:
                        print("Failed to extract captcha solution from URL.")
                except Exception as e:
                    print(f"Error extracting solution from URL: {e}")
            else:
                print("No captcha message found.")
            sleep_time = random.randint(3, 5)
            print(f"Sleeping for {sleep_time} seconds before processing the next account.")
            time.sleep(sleep_time)
        print("All accounts processed for this round.")
        main_interval_sleep = 24 * 3600
        print(f"Waiting {main_interval_sleep // 3600} hours before the next round.")
        time.sleep(main_interval_sleep)

if __name__ == "__main__":
    bot_user_id = "1235890375151849485"
    auth_file = 'auth.txt'
    proxy_file = 'proxy.txt'
    auth_data, proxy_data = load_credentials(auth_file, proxy_file)
    if not auth_data:
        print("Error: No authentication data found in auth.txt")
        exit(1)
    chat(auth_data, proxy_data)