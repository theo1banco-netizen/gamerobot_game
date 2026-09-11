import telebot, json, random, os, requests, threading, string, time, sqlite3
from telebot import types

TOKEN_BOT = "8595885482:AAGCGrct6_HEV6jiNhM2fSaIrb0BhnVVcQE"
API_LINK4M = "6aa3e8cef0d35e6a041c3f14"
WEB_HIEN_MA = "https://banup.vercel.app/" # Dán link Vercel của bạn vào đây
ADMIN_IDS = [8936805776]
GROUP_PAYOUT = -1004417764956 # ID Nhóm trả thưởng công khai

lock = threading.Lock()
KEY_FILE = "keys.json"
DB_FILE, CODE_FILE = "database.db", "codes.json" # Đã đổi users.json thành database.db

GROUPS = [
    {"name": "📢 Nhóm Trả Thưởng Công Khai", "link": "https://t.me/santruongcuoinam", "chat_id": "@santruongcuoinam"},
]

PARTNER_GROUPS = [
    "https://t.me/linkkiemtienmoney",
    "https://t.me/et88_sangame_bot?start=8936805776",
    "https://t.me/combo_today",
    "https://t.me/kiemtientelefree"
]

bot = telebot.TeleBot(TOKEN_BOT, parse_mode="HTML")

def rut_gon_link(link_dai):
    with lock:
        try:
            api = f"https://link4m.co/api-shorten/v2?api={API_LINK4M}&url={link_dai}"
            r = requests.get(api, timeout=10).json()
            return r.get("shortenedUrl", link_dai)
        except:
            return link_dai

# --- HỆ THỐNG SQLITE ĐỂ KHÔNG BỊ MẤT DỮ LIỆU ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def load_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT uid, data FROM users")
    rows = cursor.fetchall()
    conn.close()
    db = {}
    for uid, data in rows:
        db[uid] = json.loads(data)
    return db

def save_db(db):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for uid, data in db.items():
        cursor.execute("INSERT OR REPLACE INTO users (uid, data) VALUES (?, ?)", (str(uid), json.dumps(data, ensure_ascii=False)))
    conn.commit()
    conn.close()
# ------------------------------------------------

def load_codes():
    if not os.path.exists(CODE_FILE): return {}
    with open(CODE_FILE,"r",encoding="utf-8") as f: return json.load(f)

def save_codes(d):
    with open(CODE_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)

def get_user(uid, name=""):
    db=load_db(); uid=str(uid)
    if uid not in db:
        db[uid]={"name":name,"balance":0,"diamond":5,"tasks":0,"f1":[],"f2":[],"f3":[],"wallet":"","real_name":"","bank":"","history":[],"current_task":None,"ref_by":None,"banned":False,"ban_reason":"","pending_rut":None, "partner_clicks":[]}
    if name: db[uid]["name"]=name
    if "partner_clicks" not in db[uid]: db[uid]["partner_clicks"] = []
    save_db(db)
    return db

def is_admin(uid): return int(uid) in ADMIN_IDS

def check_joined(uid):
    for gr in GROUPS:
        try:
            m=bot.get_chat_member(gr["chat_id"], int(uid))
            if m.status in ['left','kicked']: return False
        except: return False
    return True

def main_menu():
    m=types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📋 Hồ Sơ","🧮 Giải Bài Toán"); m.add("💎 Nhiệm Vụ Kiếm 💎","🎮 Mini App")
    m.add("🎁 Mời Bạn Bè","💸 Rút Tiền"); m.add("📜 Lịch Sử Rút","🆘 Hỗ Trợ")
    return m

def welcome_kb():
    mk=types.InlineKeyboardMarkup(row_width=1)
    for gr in GROUPS: mk.add(types.InlineKeyboardButton(gr["name"], url=gr["link"]))
    
    mk.add(
        types.InlineKeyboardButton("🤝 Đối Tác 1", callback_data="partner_0"),
        types.InlineKeyboardButton("🤝 Đối Tác 2", callback_data="partner_1")
    )
    mk.add(
        types.InlineKeyboardButton("🤝 Đối Tác 3", callback_data="partner_2"),
        types.InlineKeyboardButton("🤝 Đối Tác 4", callback_data="partner_3")
    )
    
    mk.add(types.InlineKeyboardButton("✅ Kiểm Tra Đã Tham Gia", callback_data="check_join"))
    return mk

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    db = get_user(uid, message.from_user.first_name) 
    
    args = message.text.split()
    if len(args)>1 and args[1]!=uid and not db[uid].get("ref_by"):
        ref1=args[1]
        if ref1 in db:
            db[uid]["ref_by"]=ref1
            if uid not in db[ref1]["f1"]: db[ref1]["f1"].append(uid)
            if db[ref1].get("ref_by"):
                ref2=db[ref1]["ref_by"]
                if ref2 in db and uid not in db[ref2]["f2"]:
                    db[ref2]["f2"].append(uid)
                    if db[ref2].get("ref_by"):
                        ref3=db[ref2]["ref_by"]
                        if ref3 in db and uid not in db[ref3]["f3"]: db[ref3]["f3"].append(uid)
    save_db(db)
    if db[uid].get("banned"): bot.send_message(message.chat.id, f"🚫 Bạn bị khóa: {db[uid].get('ban_reason')}"); return
    
    if not check_joined(message.from_user.id) or len(db[uid].get("partner_clicks", [])) < 3:
        bot.send_message(message.chat.id, f"👋 Chào {message.from_user.first_name} đến với săn thưởng cuối năm!\nLàm NV kiếm thu nhập - đổi nhanh về ATM/USDT.\n\n⚠️ <b>YÊU CẦU:</b> Vào nhóm trả thưởng và <b>NHẤN VÀO ÍT NHẤT 3 NHÓM ĐỐI TÁC</b> để tiếp tục:", reply_markup=welcome_kb())
    else:
        u=db[uid]; bot.send_message(message.chat.id, f"📋 Hồ Sơ\n🧑🏼‍💻 Id: {uid}\n👤 Tên: {u['name']}\n💰 {u['balance']}đ\n💎 {u['diamond']}\n🎫 NV: {u['tasks']}", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data=="check_join")
def check_cb(call):
    db=load_db()
    uid = str(call.from_user.id)
    u = db.get(uid, {})
    clicks = u.get("partner_clicks", [])
    
    if check_joined(call.from_user.id) and len(clicks) >= 3:
        bot.send_message(call.message.chat.id, f"✅ Đã join đủ!\n📋 Hồ Sơ Id: {u['name']}", reply_markup=main_menu())
    else: 
        bot.answer_callback_query(call.id, "❌ Chưa join đủ nhóm chính hoặc CHƯA ẤN ĐỦ 3 NHÓM ĐỐI TÁC!", show_alert=True)

# --- LỆNH ADMIN / USER ---

@bot.message_handler(commands=['kiemtra'])
def kt(message):
    if not is_admin(message.from_user.id): return
    db=load_db(); args=message.text.split()
    if len(args)==1:
        txt="📊 ALL USER (50 người đầu):\n"
        for uid,u in list(db.items())[:50]: txt+=f"id {uid} | {u['name']} | {u['balance']}đ | {u['diamond']}💎 | {u.get('wallet','')}\n"
        bot.send_message(message.chat.id, txt)
    else:
        u=db.get(args[1]);
        if not u: bot.send_message(message.chat.id,"Không thấy"); return
        bot.send_message(message.chat.id, f"id {args[1]}\ntên {u['name']}\n💰{u['balance']}đ\n💎{u['diamond']}\nTK:{u['wallet']}\nTên thật:{u.get('real_name')}\nNH:{u.get('bank')}\nNV:{u['tasks']}\nF1:{len(u['f1'])} F2:{len(u['f2'])} F3:{len(u['f3'])}\nBan:{u.get('banned')}")

@bot.message_handler(commands=['rut'])
def user_rut(message):
    db=load_db(); uid=str(message.from_user.id)
    if db[uid].get("banned") or db[uid].get("pending_rut"): bot.send_message(message.chat.id,"Bạn đang có lệnh rút chờ duyệt!"); return
    parts=message.text.split(maxsplit=3)
    if len(parts)<3: bot.send_message(message.chat.id,"Dùng: /rut 5000 MBBank 123456 Nguyen Van A"); return
    try: amount=int(parts[1])
    except: return
    if amount<3000 or db[uid]["balance"]<amount: bot.send_message(message.chat.id,"Min 3000đ và phải đủ số dư"); return
    wallet= ' '.join(parts[2:]); db[uid]["balance"]-=amount; db[uid]["pending_rut"]={"amount":amount,"wallet":wallet}; db[uid]["wallet"]=wallet; save_db(db)
    for ad in ADMIN_IDS: bot.send_message(ad, f"💸 RÚT MỚI\nid {uid}\ntên {db[uid]['name']}\n💰{amount}đ\nNH/STK: {wallet}\n/duyet {uid} | /tuchoi {uid} lydo")
    bot.send_message(message.chat.id,f"Đã tạo lệnh rút {amount}đ chờ duyệt!")

@bot.message_handler(commands=['code'])
def handle_code(message):
    args=message.text.split(); db=load_db(); uid=str(message.from_user.id)
    
    if is_admin(message.from_user.id) and len(args)>=3:
        cn=args[1].upper(); rw=args[2].lower(); sl=int(args[3]) if len(args)>=4 and args[3].isdigit() else 20
        codes=load_codes(); codes[cn]={"reward":rw,"left":sl,"used_by":[]}; save_codes(codes); bot.send_message(message.chat.id,f"Tạo code {cn} {rw} SL {sl}")
    else:
        if len(args)<2: return
        codes=load_codes()
        cn=args[1].upper()
        if cn not in codes: bot.send_message(message.chat.id,"❌ Code sai"); return
        if uid in codes[cn]["used_by"]: bot.send_message(message.chat.id,"Dùng rồi"); return
        if codes[cn]["left"]<=0: bot.send_message(message.chat.id,"Hết lượt"); return
        rw=codes[cn]["reward"]; num=int(''.join(filter(str.isdigit, rw)))
        if "kimcuong" in rw: db[uid]["diamond"]+=num
        else: db[uid]["balance"]+=num
        codes[cn]["left"]-=1; codes[cn]["used_by"].append(uid); save_db(db); save_codes(codes)
        bot.send_message(message.chat.id,f"✅ Nhận {rw} từ code {cn}!")

@bot.message_handler(commands=['khoa','mokhoa','duyet','tuchoi'])
def admin_cmds_only(message):
    if not is_admin(message.from_user.id): return
    db=load_db(); args=message.text.split(maxsplit=2)
    if message.text.startswith('/khoa'):
        if len(args)>=2 and args[1] in db: db[args[1]]["banned"]=True; db[args[1]]["ban_reason"]=args[2] if len(args)>2 else ""; save_db(db); bot.send_message(message.chat.id,f"Đã khóa {args[1]}")
    elif message.text.startswith('/mokhoa'):
        if len(args)>=2 and args[1] in db: db[args[1]]["banned"]=False; save_db(db); bot.send_message(message.chat.id,f"Đã mở {args[1]}")
    elif message.text.startswith('/duyet'):
        if len(args)>=2 and args[1] in db and db[args[1]].get("pending_rut"):
            uid_user = args[1]
            am = db[uid_user]["pending_rut"]["amount"]
            user_name = db[uid_user]["name"]
            
            db[uid_user]["history"].append(f"Rút {am}đ - OK")
            db[uid_user]["pending_rut"]=None
            save_db(db)
            bot.send_message(message.chat.id,f"Duyệt {uid_user}")
            
            # Gửi tin nhắn riêng báo cho người dùng
            try: bot.send_message(int(uid_user), f"✅ Rút {am:,}đ đã duyệt!")
            except: pass
            
            # Mạ hóa ID kiểu 2727***272
            if len(uid_user) >= 6:
                masked_id = uid_user[:3] + "***" + uid_user[-3:]
            else:
                masked_id = uid_user
                
            # Gửi thông báo công khai tới Nhóm Trả Thưởng
            try:
                msg_payout = (
                    f"🎉 <b>LỆNH RÚT TIỀN THÀNH CÔNG</b> 🎉\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>Tên:</b> {user_name}\n"
                    f"🆔 <b>ID:</b> <code>{masked_id}</code>\n"
                    f"💵 <b>Rút tiền:</b> {am:,}đ\n"
                    f"📊 <b>Trạng thái:</b> Thành công 💰\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"✨ <i>Chúc mừng bạn đã nhận thưởng!</i>"
                )
                bot.send_message(GROUP_PAYOUT, msg_payout)
            except Exception as e:
                print(f"Lỗi gửi nhóm trả thưởng: {e}")

    elif message.text.startswith('/tuchoi'):
        if len(args)>=2 and args[1] in db and db[args[1]].get("pending_rut"):
            am=db[args[1]]["pending_rut"]["amount"]; db[args[1]]["balance"]+=am; db[args[1]]["history"].append(f"Rút {am}đ - Từ chối {args[2] if len(args)>2 else ''}"); db[args[1]]["pending_rut"]=None; save_db(db); bot.send_message(message.chat.id,f"Từ chối {args[1]}")

# --- GAME ---

@bot.message_handler(func=lambda m: m.text in ["📋 Hồ Sơ","🧮 Giải Bài Toán","💎 Nhiệm Vụ Kiếm 💎","🎮 Mini App","🎁 Mời Bạn Bè","💸 Rút Tiền","📜 Lịch Sử Rút","🆘 Hỗ Trợ"])
def game_menu(message):
    db=load_db(); uid=str(message.from_user.id)
    if db.get(uid,{}).get("banned"): return
    
    if not check_joined(message.from_user.id) or len(db.get(uid, {}).get("partner_clicks", [])) < 3: 
        bot.send_message(message.chat.id,"Vào đủ nhóm và nhấn ít nhất 3 đối tác đã!", reply_markup=welcome_kb()); return
        
    if db[uid].get("current_task"): bot.send_message(message.chat.id,"Làm xong nhiệm vụ hiện tại đã!"); return

    if message.text=="📋 Hồ Sơ":
        u=db[uid]; bot.send_message(message.chat.id, f"📋 Hồ Sơ\nId: {uid}\nTên: {u['name']}\n💰{u['balance']}đ | 💎{u['diamond']} | NV:{u['tasks']}")
    elif message.text=="🧮 Giải Bài Toán":
        if db[uid]["diamond"]<1: bot.send_message(message.chat.id,"Hết 💎"); return
        a,b=random.randint(10,99), random.randint(1,20); op=random.choice(['+','-','*']); ans=a+b if op=='+' else a-b if op=='-' else a*b
        db[uid]["diamond"]-=1; db[uid]["current_task"]={"type":"math","ans":ans,"tries":3}; save_db(db)
        bot.send_message(message.chat.id, f"{a}{op}{b}=? Nhập đáp án (còn 3 lượt, mất 1💎)")
    elif message.text=="💎 Nhiệm Vụ Kiếm 💎":
        mk=types.InlineKeyboardMarkup(); mk.add(types.InlineKeyboardButton("🎬 Xem QC", callback_data="maintain"), types.InlineKeyboardButton("📎 Vượt Link", callback_data="vuotlink"))
        bot.send_message(message.chat.id,"Chọn NV:", reply_markup=mk)
    elif message.text=="🎁 Mời Bạn Bè":
        link=f"https://t.me/{bot.get_me().username}?start={uid}"; bot.send_message(message.chat.id, f"Link ref: {link}\nF1({len(db[uid]['f1'])}) 20đ+3💎\nF2({len(db[uid]['f2'])}) 10đ+2💎\nF3({len(db[uid]['f3'])}) 5đ+1💎\nĐủ 5 NV mới tính!")
    elif message.text=="💸 Rút Tiền":
        bot.send_message(message.chat.id,"Gõ: /rut 5000 MBBank 123456 Nguyen Van A\nMin 3000đ\nVí dụ TON/USDT cũng ghi vào")
    elif message.text=="🎮 Mini App": bot.send_message(message.chat.id,"🛠️ Mini App đang bảo trì")
    elif message.text=="📜 Lịch Sử Rút": bot.send_message(message.chat.id, str(db[uid]["history"] or "Chưa có"))
    elif message.text=="🆘 Hỗ Trợ": bot.send_message(message.chat.id,"CSKH: @admin")

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    if call.data.startswith("partner_"):
        idx = int(call.data.split("_")[1])
        db = load_db()
        uid = str(call.from_user.id)
        
        if "partner_clicks" not in db[uid]: db[uid]["partner_clicks"] = []
        if idx not in db[uid]["partner_clicks"]:
            db[uid]["partner_clicks"].append(idx)
            save_db(db)
            
        bot.answer_callback_query(call.id, "✅ Đã ghi nhận click!")
        bot.send_message(call.message.chat.id, f"👉 Link tham gia Đối Tác {idx+1}: {PARTNER_GROUPS[idx]}")
        return

    if call.data=="maintain": bot.answer_callback_query(call.id,"⚒️ Đang bảo trì!",show_alert=True)
    if call.data=="vuotlink":
        db=load_db(); uid=str(call.from_user.id)
        if db[uid].get("current_task"): return
        
        length = random.choice([8,9])
        ma = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        
        with lock:
            keys = json.load(open(KEY_FILE)) if os.path.exists(KEY_FILE) else {}
            keys[ma] = {"owner": str(uid), "created": time.time(), "used": False}
            with open(KEY_FILE, "w", encoding="utf-8") as f:
                json.dump(keys, f, ensure_ascii=False, indent=2)

        db[uid]["current_task"]={"type":"link","code":ma}; save_db(db)
        
        link_dai = f"{WEB_HIEN_MA}/?c={ma}"
        link_short = rut_gon_link(link_dai)
        
        mk=types.InlineKeyboardMarkup(); mk.add(types.InlineKeyboardButton("▶️ Bắt Đầu", url=link_short))
        bot.send_message(call.message.chat.id, f"Link vượt: {link_short}\nLấy mã {length} chữ rồi quay lại nhập nhé! +2💎", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.text not in ["📋 Hồ Sơ","🧮 Giải Bài Toán","💎 Nhiệm Vụ Kiếm 💎","🎮 Mini App","🎁 Mời Bạn Bè","💸 Rút Tiền","📜 Lịch Sử Rút","🆘 Hỗ Trợ"] and load_db().get(str(m.from_user.id),{}).get("current_task"))
def check_task(message):
    db=load_db(); uid=str(message.from_user.id); task=db[uid].get("current_task")
    if not task: return
    if task["type"]=="math":
        try:
            if int(message.text.strip())==task["ans"]:
                db[uid]["balance"]+=40; db[uid]["current_task"]=None; save_db(db); bot.send_message(message.chat.id,"✅ Đúng +40đ", reply_markup=main_menu())
            else:
                task["tries"]-=1
                if task["tries"]<=0: db[uid]["current_task"]=None; bot.send_message(message.chat.id,"❌ Sai hết lượt!")
                else: bot.send_message(message.chat.id,f"❌ Sai còn {task['tries']} lượt")
                save_db(db)
        except: bot.send_message(message.chat.id,"Nhập số thôi")
    elif task["type"]=="link":
        input_code = message.text.strip().upper()
        if input_code==task["code"]:
            with lock:
                if os.path.exists(KEY_FILE):
                    try:
                        with open(KEY_FILE, "r", encoding="utf-8") as f:
                            keys = json.load(f)
                        if input_code in keys:
                            del keys[input_code]
                            with open(KEY_FILE, "w", encoding="utf-8") as f:
                                json.dump(keys, f, ensure_ascii=False, indent=2)
                    except: pass

            db[uid]["diamond"]+=2; db[uid]["tasks"]+=1; db[uid]["current_task"]=None
            if db[uid]["tasks"]==5 and db[uid].get("ref_by"):
                ref1=db[uid]["ref_by"]
                if ref1 in db: db[ref1]["balance"]+=20; db[ref1]["diamond"]+=3
                if db.get(ref1,{}).get("ref_by"):
                    ref2=db[ref1]["ref_by"]
                    if ref2 in db: db[ref2]["balance"]+=10; db[ref2]["diamond"]+=2
                    if db.get(ref1,{}).get("ref_by"):
                        ref3=db[ref2]["ref_by"]
                        if ref3 in db: db[ref3]["balance"]+=5; db[ref3]["diamond"]+=1
            save_db(db); bot.send_message(message.chat.id,"✅ Mã đúng +2💎", reply_markup=main_menu())
        else: bot.send_message(message.chat.id,"❌ Mã sai!")

bot.infinity_polling()