import os
import re
import time
import shlex
import random
import string as _string
from datetime import date, timedelta

import paramiko
from telethon import events, Button
from telegram import ParseMode

import handlers.client
import env.env

client = handlers.client.client
botClient = handlers.client.botClient

IP = env.env.host
PORT = 22
bot_name = env.env.bot_name
USERNAME = env.env.username
PASSWORD = env.env.password
LIST_OF_ADMINS = env.env.LIST_OF_ADMINS
BANNER_NAME = env.env.BANNER_NAME

# Authorized Telegram user ids. ADMINS may be a single id or a
# comma/space separated list of ids.
ADMIN_IDS = {
    part.strip()
    for part in re.split(r'[,\s]+', LIST_OF_ADMINS or '')
    if part.strip()
}

# Input validation. These values are interpolated into shell commands that
# run as root on the remote host, so they must be strictly validated.
USERNAME_RE = re.compile(r'^[a-z_][a-z0-9_-]{0,31}$')
PASSWORD_RE = re.compile(r'^[A-Za-z0-9_@%+=:,./-]{1,64}$')
LIMIT_RE = re.compile(r'^[0-9]{1,4}$')


def is_admin(user_id):
    return str(user_id) in ADMIN_IDS


def _new_ssh_client():
    """Return an SSHClient that verifies the server host key.

    The remote host key must be present in the system or user known_hosts
    file. Add it once with e.g. ``ssh-keyscan -H <host> >> ~/.ssh/known_hosts``.
    ``AutoAddPolicy`` is intentionally NOT used because it silently trusts
    any key and enables man-in-the-middle attacks.
    """
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    known_hosts = os.path.expanduser('~/.ssh/known_hosts')
    if os.path.exists(known_hosts):
        try:
            ssh.load_host_keys(known_hosts)
        except (IOError, OSError):
            pass
    ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
    return ssh


@botClient.on(events.InlineQuery)
async def iquery(query):
    result = query.builder.article(
        'menu',
        text="Select..",
        parse_mode=ParseMode.HTML,
        link_preview=False,
        buttons=[
            [Button.inline("🛰 User 🛰", data="sshuser")],
            [Button.inline("🚀 Test User🚀", data="testuser")],
            [Button.inline("❌ close ❌", data="closem")],
        ],
    )
    await query.answer([result])


@events.register(events.NewMessage(outgoing=True, pattern=r'\.menu'))
async def menu(event):
    chat = await event.get_chat()
    await client.delete_messages(chat, event.message)
    results = await client.inline_query(f'{bot_name}', 'menu')
    await results[0].click(event.chat_id)


@botClient.on(events.callbackquery.CallbackQuery(data="closem"))
async def callback(event):
    if is_admin(event.original_update.user_id):
        await event.edit('[🧿YOU Tech🧿](https://t.me/YouTech_VPN_HUB)', parse_mode="markdown")
    else:
        await event.answer("you cant")


@botClient.on(events.CallbackQuery)
async def calllback(event):
    if is_admin(event.original_update.user_id):
        if event.data == b'sshuser':
            await event.answer(
                "🎯CREATE USER🎯 - .ssh + username/password/Expire days/limit\n"
                " EG:- .ssh sbatrow/sbatrow/30/2",
                alert=True,
            )
        if event.data == b'testuser':
            await event.answer(
                "🎯CREATE TEST🎯 - .utest + Expired hours\n EG:- .utest 1",
                alert=True,
            )
    else:
        await event.answer("you cant")


@client.on(events.NewMessage(pattern=r'\.ssh (\S+)'))
async def cmd(event):
    # Only authorized admins may create accounts.
    if not (event.out or is_admin(event.sender_id)):
        return

    parts = event.raw_text.split()
    if len(parts) <= 1:
        await event.edit('❌ Usage: .ssh username/password/days/limit ❌')
        return

    fields = parts[1].split('/')
    if len(fields) < 4:
        await event.edit('❌ Usage: .ssh username/password/days/limit ❌')
        return

    username, password, days_raw, sshlimit = fields[0], fields[1], fields[2], fields[3]

    if not USERNAME_RE.match(username):
        await event.edit('❌ Invalid username ❌')
        return
    if not PASSWORD_RE.match(password):
        await event.edit('❌ Invalid password ❌')
        return
    if not LIMIT_RE.match(sshlimit):
        await event.edit('❌ Invalid limit ❌')
        return
    try:
        dias = int(days_raw)
    except ValueError:
        await event.edit('❌ Invalid number of days ❌')
        return
    if not 0 < dias <= 3650:
        await event.edit('❌ Invalid number of days ❌')
        return

    Begindatestring = date.today()

    check = _new_ssh_client()
    check.connect(IP, PORT, USERNAME, PASSWORD)
    check_user = check.invoke_shell()
    check_user.send("sudo -s\n")
    check_user.send("cd\n")
    check_user.send("cat /root/usuarios.db\n")
    time.sleep(1)
    output = check_user.recv(6553)
    vl = output.decode('ascii')
    check.close()

    if username in vl:
        await event.edit('❌ Username already in use ❌')
        return

    await event.edit('⚙️ Creating an account... ⚙️')

    user_q = shlex.quote(username)
    pass_q = shlex.quote(password)
    limit_q = shlex.quote(sshlimit)

    session = _new_ssh_client()
    session.connect(IP, PORT, USERNAME, PASSWORD)
    remote_connection = session.invoke_shell()
    remote_connection.send("sudo -s\n")
    remote_connection.send("cd\n")
    remote_connection.send(f"""final=$(date "+%Y-%m-%d" -d "+{dias} days")\n""")
    remote_connection.send(f"""gui=$(date "+%d/%m/%Y" -d "+{dias} days")\n""")
    remote_connection.send(f"""pass=$(perl -e 'print crypt($ARGV[0], "password")' {pass_q})\n""")
    remote_connection.send(
        f"""useradd -e $final -M -s /bin/false -p $pass {user_q} >/dev/null 2>&1 & echo {pass_q} >/etc/DARKssh/senha/{user_q}\n"""
    )
    remote_connection.send(f"""echo {user_q} {limit_q} >>/root/usuarios.db\n""")
    remote_connection.send("""\n""")
    time.sleep(1)
    Enddate = Begindatestring + timedelta(days=dias)
    await event.edit(
        f'♻️Paid Privet SSH ♻️\n\n**{BANNER_NAME}**\n======================\n'
        f'=❌NO SPAM\n=❌NO DDOS\n=❌NO HACKING\n=❌NO CARDING\n=❌NO TORRENT\n'
        f'=❌NO OVER DOWNLOAD\n=❌NO MULTILOGIN\n=======================\n\n\n'
        f'ᗚ IP • ๛ `{IP}`\nᗚ Username • ๛ `{username}`\nᗚ Password • ๛ `{password}`\n'
        f'ᗚ Limit • {sshlimit}\nᗚ Expire • {Enddate}\n\n'
        f'࿂ SSH •  22\n࿂ SSL •  443\n࿂ Squid  •  8080\n࿂ Dropbear •  80\n'
        f'[-] ═───────◇───────═\n࿂ Badvpn •  7300\n[-] ═───────◇───────═\n'
        f'›☬[•] SCRIPTS ═◇ DARKSSH ◇═ [•]☬',
        parse_mode="markdown",
    )
    session.close()


@client.on(events.NewMessage(pattern=r'\.utest (\S+)'))
async def test(event):
    # Only authorized admins may create test accounts.
    if not (event.out or is_admin(event.sender_id)):
        return

    parts = event.raw_text.split()
    if len(parts) <= 1:
        await event.edit('❌ Usage: .utest hours ❌')
        return
    try:
        teh = int(parts[1])
    except ValueError:
        await event.edit('❌ Invalid number of hours ❌')
        return
    if not 0 < teh <= 168:
        await event.edit('❌ Invalid number of hours ❌')
        return

    await event.edit('⚙️ Creating an account... ⚙️')

    x = ''.join(random.choices(_string.ascii_letters + _string.digits, k=5))

    session = _new_ssh_client()
    session.connect(IP, PORT, USERNAME, PASSWORD)
    remote_connection = session.invoke_shell()
    remote_connection.send("sudo -s\n")
    remote_connection.send("cd\n")
    remote_connection.send(f""" 
    usuario='{x}'
    senha='1234'
    limite='1'
    ex_date=$(date '+%d/%m/%C%y' -d " +2 days")
    tuserdate=$(date '+%C%y/%m/%d' -d " +2 days")
    """)
    remote_connection.send("""

    /usr/sbin/useradd -M -N -s /bin/false $usuario -e $tuserdate >/dev/null 2>&1
    (
        echo "$senha"
        echo "$senha"
    ) | passwd $usuario >/dev/null 2>&1
    echo "$senha" >/etc/DARKssh/senha/$usuario
    echo "$usuario $limite" >>/root/usuarios.db
    [[ "${message_from_id[$id]}" != "$id_admin" ]] && {
        echo "$usuario:$senha:$ex_date:$limite" >/etc/bot/revenda/${message_from_username}/usuarios/$usuario
    }
    dir_teste="/etc/bot/revenda/${message_from_username}/usuarios/$usuario"
    cat <<-EOF >/etc/DARKssh/userteste/$usuario.sh
    """)
    remote_connection.send(f"""
	#!/bin/bash
	# USUARIO TESTE
	[[ \$(ps -u "$usuario" | grep -c sshd) != '0' ]] && pkill -u $usuario
	userdel --force $usuario
	grep -v ^$usuario[[:space:]] /root/usuarios.db > /tmp/ph ; cat /tmp/ph > /root/usuarios.db
	[[ -e $dir_teste ]] && rm $dir_teste
	rm /etc/DARKssh/senha/$usuario > /dev/null 2>&1
	rm /etc/DARKssh/userteste/$usuario.sh
	EOF
    chmod +x /etc/DARKssh/userteste/$usuario.sh
    echo "/etc/DARKssh/userteste/$usuario.sh" | at now + {teh} hour >/dev/null 2>&1
    [[ "{teh}" == '1' ]] && hrs="hora" || hrs="horas"
    [[ "$(ls /etc/bot/arquivos | wc -l)" != '0' ]]
    """)
    await event.edit(
        f'♻️Paid Privet SSH ♻️\n\n**{BANNER_NAME}**\n======================\n'
        f'=❌NO SPAM\n=❌NO DDOS\n=❌NO HACKING\n=❌NO CARDING\n=❌NO TORRENT\n'
        f'=❌NO OVER DOWNLOAD\n=❌NO MULTILOGIN\n=======================\n\n\n'
        f'ᗚ IP • ๛ `{IP}`\nᗚ Username • ๛ `{x}`\nᗚ Password • ๛ `1234`\n'
        f'ᗚ Limit • 1\nᗚ Expire • {teh} Hr\n\n'
        f'࿂ SSH •  22\n࿂ SSL •  443\n࿂ Squid  •  8080\n࿂ Dropbear •  80\n'
        f'[-] ═───────◇───────═\n࿂ Badvpn •  7300\n[-] ═───────◇───────═\n'
        f'›☬[•] SCRIPTS ═◇ DARKSSH ◇═ [•]☬',
        parse_mode="markdown",
    )
    time.sleep(1)
    session.close()
