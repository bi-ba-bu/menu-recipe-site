"""
seed.py — 菜品库种子数据（由前端 data.js 迁移而来）

字段与前端展示一一对应：
    name / subtitle / desc / cover / emoji    基本信息与头图
    time / difficulty / serving               时长、难度、份量
    tags                                      标签
    nutrition                                 {calorie, protein, fat, carb, fiber}
    ingredients                               [{name, amount, main}]
    steps                                     [{title, desc, minutes}]
    tips                                      小贴士

生成方式：由 menu-recipe-site/js/data.js 导出后转写，保证前后端菜品完全一致。
如需修改菜品，直接编辑本文件后重启服务即可。
"""

from __future__ import annotations

from typing import Any

RECIPES: dict[str, dict[str, Any]] = {
    "tomato-beef": {
        "name": "番茄炖牛腩",
        "subtitle": "酸甜浓郁 · 炖到入口即化",
        "desc": "牛腩先煎后炖，收汁前放番茄块保酸感，全程小火慢煨 1 小时以上。",
        "cover": "linear-gradient(135deg, #ff9a76 0%, #d64545 100%)",
        "emoji": "🍲",
        "time": 75,
        "difficulty": "中等",
        "serving": "2-3 人份",
        "tags": ["meat", "soup", "warming"],
        "nutrition": {
            "calorie": 385,
            "protein": 32,
            "fat": 22,
            "carb": 14,
            "fiber": 3.2,
        },
        "ingredients": [
            {
                "name": "牛腩",
                "amount": "500 g",
                "main": True,
            },
            {
                "name": "中等番茄",
                "amount": "3 个",
                "main": True,
            },
            {
                "name": "洋葱",
                "amount": "半个",
            },
            {
                "name": "姜片",
                "amount": "4 片",
            },
            {
                "name": "八角 / 桂皮",
                "amount": "各 1 个",
            },
            {
                "name": "番茄膏",
                "amount": "1 勺",
            },
            {
                "name": "盐",
                "amount": "3 g",
            },
            {
                "name": "冰糖",
                "amount": "5 g",
            },
        ],
        "steps": [
            {
                "title": "牛腩焯水",
                "desc": "牛腩切 3 cm 块，冷水下锅，加姜片与料酒，水开后撇净浮沫，煮 3 分钟捞出冲净。",
                "minutes": 8,
            },
            {
                "title": "煎出脂香",
                "desc": "锅内少油，牛腩块中火煎至表面微焦，帮助锁住肉汁并逼出油脂。",
                "minutes": 6,
            },
            {
                "title": "炒香底味",
                "desc": "下洋葱、姜片、八角桂皮炒香，加番茄膏炒出红油，再放一半番茄块炒软出水。",
                "minutes": 5,
            },
            {
                "title": "小火慢炖",
                "desc": "加开水没过牛腩 3 cm，加冰糖，大火烧开后转最小火加盖炖 55 分钟。",
                "minutes": 55,
            },
            {
                "title": "收汁出锅",
                "desc": "放入剩余番茄块再炖 6 分钟保留果肉口感，加盐调味，收至汤汁略稠。",
                "minutes": 6,
            },
        ],
        "tips": "番茄分两次放：前半程给底味，后半程给果肉。中途水不够只加热水，避免肉质骤缩变柴。",
    },
    "garlic-broccoli": {
        "name": "蒜蓉西兰花",
        "subtitle": "30 秒快炒 · 保持翠绿",
        "desc": "西兰花先盐水浸泡，焯水时加油盐锁色，急火快炒不超过 1 分钟。",
        "cover": "linear-gradient(135deg, #a8e063 0%, #2f8f4e 100%)",
        "emoji": "🥦",
        "time": 10,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["veg", "light", "quick"],
        "nutrition": {
            "calorie": 96,
            "protein": 5.2,
            "fat": 5.8,
            "carb": 7.6,
            "fiber": 4.1,
        },
        "ingredients": [
            {
                "name": "西兰花",
                "amount": "1 颗 (约 400 g)",
                "main": True,
            },
            {
                "name": "大蒜",
                "amount": "4 瓣",
                "main": True,
            },
            {
                "name": "盐",
                "amount": "2 g",
            },
            {
                "name": "食用油",
                "amount": "1 勺",
            },
            {
                "name": "生抽",
                "amount": "半勺",
            },
        ],
        "steps": [
            {
                "title": "改刀洗净",
                "desc": "西兰花切小朵，淡盐水浸泡 5 分钟后冲洗干净，沥干水分。",
                "minutes": 6,
            },
            {
                "title": "焯水锁色",
                "desc": "水开加少许盐和油，下西兰花焯 40 秒，立刻过凉水保持脆嫩。",
                "minutes": 2,
            },
            {
                "title": "爆香蒜末",
                "desc": "热锅冷油下蒜末，小火煸至微微金黄出香，注意别炒糊。",
                "minutes": 1,
            },
            {
                "title": "急火成菜",
                "desc": "下西兰花大火翻炒 40 秒，沿锅边烹入生抽，加盐翻匀即可出锅。",
                "minutes": 1,
            },
        ],
        "tips": "焯水后的西兰花一定沥干，带水下锅会变成\"煮\"，脆感和颜色都会损失。",
    },
    "steamed-fish": {
        "name": "清蒸鲈鱼",
        "subtitle": "鲜嫩不腥 · 15 分钟上桌",
        "desc": "鲈鱼蒸前抹盐静置去腥，蒸 8 分钟关火虚蒸 2 分钟，再淋热油激香。",
        "cover": "linear-gradient(135deg, #89f7fe 0%, #3b82f6 100%)",
        "emoji": "🐟",
        "time": 20,
        "difficulty": "简单",
        "serving": "2-3 人份",
        "tags": ["light", "meat", "quick"],
        "nutrition": {
            "calorie": 240,
            "protein": 34,
            "fat": 9,
            "carb": 3,
            "fiber": 0.4,
        },
        "ingredients": [
            {
                "name": "新鲜鲈鱼",
                "amount": "1 条 (约 600 g)",
                "main": True,
            },
            {
                "name": "姜丝 / 葱段",
                "amount": "适量",
                "main": True,
            },
            {
                "name": "蒸鱼豉油",
                "amount": "3 勺",
            },
            {
                "name": "料酒",
                "amount": "1 勺",
            },
            {
                "name": "食用油",
                "amount": "2 勺",
            },
        ],
        "steps": [
            {
                "title": "处理鱼身",
                "desc": "鱼去内脏洗净，两面各划 3 刀，用料酒和少许盐抹匀，腹内塞姜片葱段腌 5 分钟。",
                "minutes": 6,
            },
            {
                "title": "垫葱蒸制",
                "desc": "盘底铺葱段姜片放鱼，水开后上锅，大火蒸 8 分钟。",
                "minutes": 8,
            },
            {
                "title": "虚蒸定型",
                "desc": "关火后不要开盖，虚蒸 2 分钟让鱼肉纤维松弛，倒掉盘中腥水。",
                "minutes": 2,
            },
            {
                "title": "淋油激香",
                "desc": "铺上新鲜葱丝，淋蒸鱼豉油，最后浇一勺滚烫热油激出香气。",
                "minutes": 2,
            },
        ],
        "tips": "判断熟度：用筷子轻戳鱼身最厚处，能顺畅插入即熟，多蒸会变干。",
    },
    "mapo-tofu": {
        "name": "家常麻婆豆腐",
        "subtitle": "麻辣鲜香 · 一碗下饭",
        "desc": "豆腐先用淡盐水焯过定型，分三次勾芡让汤汁牢牢挂在豆腐上。",
        "cover": "linear-gradient(135deg, #ff6a6a 0%, #b91c1c 100%)",
        "emoji": "🌶️",
        "time": 18,
        "difficulty": "中等",
        "serving": "2 人份",
        "tags": ["veg", "spicy"],
        "nutrition": {
            "calorie": 265,
            "protein": 16,
            "fat": 18,
            "carb": 11,
            "fiber": 1.8,
        },
        "ingredients": [
            {
                "name": "嫩豆腐",
                "amount": "1 盒 (400 g)",
                "main": True,
            },
            {
                "name": "牛肉末",
                "amount": "80 g",
            },
            {
                "name": "郫县豆瓣酱",
                "amount": "1 勺",
                "main": True,
            },
            {
                "name": "花椒粉",
                "amount": "1 茶勺",
            },
            {
                "name": "蒜末 / 姜末",
                "amount": "各 1 勺",
            },
            {
                "name": "水淀粉",
                "amount": "3 勺",
            },
        ],
        "steps": [
            {
                "title": "豆腐定形",
                "desc": "豆腐切 2 cm 方块，入淡盐沸水焯 1 分钟捞出，去除豆腥并增加韧性。",
                "minutes": 3,
            },
            {
                "title": "炒酥肉末",
                "desc": "热锅少油下肉末，中火炒散炒酥，逼出油香后盛出备用。",
                "minutes": 4,
            },
            {
                "title": "熬出红油",
                "desc": "底油下豆瓣酱与姜蒜末，小火慢炒 1 分钟至出红油，加清水烧开。",
                "minutes": 2,
            },
            {
                "title": "入豆腐勾芡",
                "desc": "下豆腐与肉末小火煮 3 分钟，分三次淋水淀粉并轻推，让汤汁包裹豆腐。",
                "minutes": 5,
            },
            {
                "title": "撒花椒出锅",
                "desc": "关火后撒花椒粉与葱花，趁热上桌。",
                "minutes": 1,
            },
        ],
        "tips": "全程用推勺、不要翻炒，见方不散的豆腐才是成功标志。",
    },
    "oat-congee": {
        "name": "牛奶燕麦粥",
        "subtitle": "5 分钟快手早餐",
        "desc": "燕麦小火煮到稠滑后关火再倒牛奶，避免长时间沸煮破坏口感。",
        "cover": "linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%)",
        "emoji": "🥣",
        "time": 10,
        "difficulty": "简单",
        "serving": "1 人份",
        "tags": ["light", "staple", "quick"],
        "nutrition": {
            "calorie": 220,
            "protein": 9.5,
            "fat": 5.2,
            "carb": 34,
            "fiber": 4.5,
        },
        "ingredients": [
            {
                "name": "即食燕麦片",
                "amount": "40 g",
                "main": True,
            },
            {
                "name": "牛奶",
                "amount": "250 ml",
                "main": True,
            },
            {
                "name": "香蕉",
                "amount": "半根",
            },
            {
                "name": "坚果碎",
                "amount": "1 勺",
            },
        ],
        "steps": [
            {
                "title": "煮燕麦",
                "desc": "燕麦加 100 ml 清水，小火煮 3 分钟至粘稠，期间搅拌防粘底。",
                "minutes": 3,
            },
            {
                "title": "加牛奶",
                "desc": "关火倒入牛奶搅匀，用余温加热，避免牛奶沸煮起泡溢锅。",
                "minutes": 2,
            },
            {
                "title": "铺料装盘",
                "desc": "盛出后铺香蕉片，撒坚果碎，喜欢甜口可加少许蜂蜜。",
                "minutes": 1,
            },
        ],
        "tips": "想更省时间可用\"隔夜燕麦\"做法：前晚燕麦加牛奶冷藏，早上直接加水果。",
    },
    "kung-pao-chicken": {
        "name": "宫保鸡丁",
        "subtitle": "酸甜微辣 · 荔枝口味",
        "desc": "鸡丁先上浆滑油，宫保汁提前调匀，起锅前 30 秒一次淋入。",
        "cover": "linear-gradient(135deg, #fbc687 0%, #d97706 100%)",
        "emoji": "🍗",
        "time": 25,
        "difficulty": "中等",
        "serving": "2 人份",
        "tags": ["meat", "spicy"],
        "nutrition": {
            "calorie": 320,
            "protein": 26,
            "fat": 17,
            "carb": 15,
            "fiber": 2.6,
        },
        "ingredients": [
            {
                "name": "鸡腿肉",
                "amount": "300 g",
                "main": True,
            },
            {
                "name": "油酥花生",
                "amount": "50 g",
                "main": True,
            },
            {
                "name": "干辣椒",
                "amount": "8 个",
            },
            {
                "name": "花椒",
                "amount": "1 茶勺",
            },
            {
                "name": "葱白",
                "amount": "4 段",
            },
            {
                "name": "宫保汁（醋:糖:生抽 = 2:2:1）",
                "amount": "4 勺",
            },
        ],
        "steps": [
            {
                "title": "上浆腌制",
                "desc": "鸡腿肉切 1.5 cm 丁，加盐、料酒、蛋清、淀粉抓匀腌 10 分钟。",
                "minutes": 10,
            },
            {
                "title": "滑散鸡丁",
                "desc": "五成热油下鸡丁，快速划散至变白断生，捞出控油。",
                "minutes": 3,
            },
            {
                "title": "炒香干料",
                "desc": "底油小火煸干辣椒与花椒至出香呈棕红，加葱白姜蒜炒匀。",
                "minutes": 2,
            },
            {
                "title": "合炒收汁",
                "desc": "倒回鸡丁，沿锅边淋入宫保汁大火快炒，汁水挂匀后加花生翻两下出锅。",
                "minutes": 3,
            },
        ],
        "tips": "花生最后放才酥脆；宫保汁必须提前调好，避免逐样加料导致火候过头。",
    },
    "braised-pork": {
        "name": "土豆红烧肉",
        "subtitle": "浓油赤酱 · 下饭担当",
        "desc": "五花肉冷水下锅焯透，炒糖色上色后与土豆同炖，土豆后放防糊锅。",
        "cover": "linear-gradient(135deg, #f6d365 0%, #a0522d 100%)",
        "emoji": "🥘",
        "time": 60,
        "difficulty": "中等",
        "serving": "3-4 人份",
        "tags": ["meat", "warming"],
        "nutrition": {
            "calorie": 480,
            "protein": 24,
            "fat": 36,
            "carb": 22,
            "fiber": 2.1,
        },
        "ingredients": [
            {
                "name": "五花肉",
                "amount": "500 g",
                "main": True,
            },
            {
                "name": "土豆",
                "amount": "2 个 (约 400 g)",
                "main": True,
            },
            {
                "name": "冰糖",
                "amount": "20 g",
            },
            {
                "name": "生抽 / 老抽",
                "amount": "各 1.5 勺",
            },
            {
                "name": "八角 / 香叶",
                "amount": "各 1 个",
            },
        ],
        "steps": [
            {
                "title": "焯水去杂",
                "desc": "五花肉切 3 cm 块，冷水下锅开火，水开后煮 3 分钟捞出温水洗净。",
                "minutes": 6,
            },
            {
                "title": "炒出糖色",
                "desc": "锅中小火化开冰糖至琥珀色，倒入肉块翻炒上色。",
                "minutes": 5,
            },
            {
                "title": "调味炖煮",
                "desc": "加姜葱、八角香叶、生抽老抽，加开水没过肉，小火炖 30 分钟。",
                "minutes": 30,
            },
            {
                "title": "加土豆同炖",
                "desc": "下滚刀土豆块再炖 15 分钟至软糯，最后大火收汁。",
                "minutes": 15,
            },
        ],
        "tips": "糖色宁可浅一点也别炒过，焦味一旦产生整锅都会发苦。",
    },
    "dumplings": {
        "name": "白菜猪肉水饺",
        "subtitle": "手作家常 · 鲜汁不流",
        "desc": "白菜剁碎后要盐渍挤水，肉馅打水上劲，包出来才多汁不散。",
        "cover": "linear-gradient(135deg, #fef6e4 0%, #c9ada7 100%)",
        "emoji": "🥟",
        "time": 40,
        "difficulty": "进阶",
        "serving": "约 30 个",
        "tags": ["staple", "meat"],
        "nutrition": {
            "calorie": 430,
            "protein": 20,
            "fat": 16,
            "carb": 52,
            "fiber": 3,
        },
        "ingredients": [
            {
                "name": "中筋面粉",
                "amount": "300 g",
                "main": True,
            },
            {
                "name": "猪肉馅",
                "amount": "300 g",
                "main": True,
            },
            {
                "name": "白菜",
                "amount": "半颗",
            },
            {
                "name": "姜末 / 花椒水",
                "amount": "各适量",
            },
            {
                "name": "生抽 / 香油",
                "amount": "各 1 勺",
            },
        ],
        "steps": [
            {
                "title": "和面醒面",
                "desc": "面粉加 150 ml 温水揉成光滑面团，覆保鲜膜醒 20 分钟。",
                "minutes": 20,
            },
            {
                "title": "调馅打水",
                "desc": "肉馅分次加花椒水同一方向搅打上劲，混入挤干水的白菜碎，加调料拌匀。",
                "minutes": 8,
            },
            {
                "title": "擀皮包制",
                "desc": "面团搓条切剂，擀成中厚边薄的圆皮，包入馅料捏成饺子。",
                "minutes": 15,
            },
            {
                "title": "点水煮熟",
                "desc": "水开下饺子，煮沸后点两次凉水，饺子浮起鼓胀即熟。",
                "minutes": 8,
            },
        ],
        "tips": "白菜挤水留半小碗菜汁，拌馅时回加两勺，鲜味最足。",
    },
    "beef-noodle": {
        "name": "红烧牛肉面",
        "subtitle": "汤头醇厚 · 慢炖 90 分钟",
        "desc": "牛腱子焯水后与豆瓣酱同炒，加香辛料小火慢炖，汤面分离更清爽。",
        "cover": "linear-gradient(135deg, #d1913c 0%, #7c2d12 100%)",
        "emoji": "🍜",
        "time": 100,
        "difficulty": "进阶",
        "serving": "2 人份",
        "tags": ["staple", "meat", "warming"],
        "nutrition": {
            "calorie": 520,
            "protein": 30,
            "fat": 18,
            "carb": 58,
            "fiber": 2.4,
        },
        "ingredients": [
            {
                "name": "牛腱子肉",
                "amount": "500 g",
                "main": True,
            },
            {
                "name": "手擀面",
                "amount": "300 g",
                "main": True,
            },
            {
                "name": "豆瓣酱",
                "amount": "1 勺",
            },
            {
                "name": "草果 / 香叶 / 桂皮",
                "amount": "适量",
            },
            {
                "name": "小白菜",
                "amount": "2 棵",
            },
        ],
        "steps": [
            {
                "title": "浸出血水",
                "desc": "牛腱切大块冷水浸泡 30 分钟，中途换水一次。",
                "minutes": 30,
            },
            {
                "title": "焯水炒香",
                "desc": "冷水下锅焯透后捞出，与豆瓣酱、姜片同炒出红油。",
                "minutes": 8,
            },
            {
                "title": "慢炖成汤",
                "desc": "加开水与香料，小火炖 60 分钟至筷子可插入，加盐调味。",
                "minutes": 60,
            },
            {
                "title": "煮面组装",
                "desc": "另起锅煮面 3 分钟，烫菜，浇上牛肉与热汤即可。",
                "minutes": 5,
            },
        ],
        "tips": "面与汤分开煮：面汤里淀粉多，混在一起汤会浑，口感也糊。",
    },
    "shrimp-noodle": {
        "name": "鲜虾蔬菜面",
        "subtitle": "清甜海味 · 20 分钟",
        "desc": "虾头煸出虾油做汤底，鲜味翻倍，蔬菜后放保持脆嫩。",
        "cover": "linear-gradient(135deg, #ffd3a5 0%, #fd6585 100%)",
        "emoji": "🍤",
        "time": 20,
        "difficulty": "简单",
        "serving": "1-2 人份",
        "tags": ["staple", "light", "quick"],
        "nutrition": {
            "calorie": 360,
            "protein": 22,
            "fat": 9,
            "carb": 46,
            "fiber": 2.8,
        },
        "ingredients": [
            {
                "name": "鲜虾",
                "amount": "8 只",
                "main": True,
            },
            {
                "name": "细面条",
                "amount": "150 g",
                "main": True,
            },
            {
                "name": "小青菜",
                "amount": "3 棵",
            },
            {
                "name": "鸡蛋",
                "amount": "1 个",
            },
            {
                "name": "姜片",
                "amount": "2 片",
            },
        ],
        "steps": [
            {
                "title": "处理鲜虾",
                "desc": "虾去壳留头，虾身开背去虾线，用少许盐和白胡椒腌 3 分钟。",
                "minutes": 5,
            },
            {
                "title": "煸出虾油",
                "desc": "热油下虾头姜片小火煸 2 分钟至壳变红出油，加 500 ml 水煮 5 分钟。",
                "minutes": 7,
            },
            {
                "title": "煮面配菜",
                "desc": "捞出虾头，下盐调味，放入面条煮至八成熟后加青菜与虾仁。",
                "minutes": 4,
            },
            {
                "title": "卧蛋出锅",
                "desc": "打入鸡蛋煮成荷包蛋，撒葱花与白胡椒即可。",
                "minutes": 3,
            },
        ],
        "tips": "虾仁最后 1 分钟再下，久煮会缩水变硬。",
    },
    "millet-porridge": {
        "name": "小米南瓜粥",
        "subtitle": "温润养胃 · 清晨一碗",
        "desc": "小米与南瓜先蒸后煮，口感绵密不需额外加糖。",
        "cover": "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
        "emoji": "🎃",
        "time": 25,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["light", "staple", "warming"],
        "nutrition": {
            "calorie": 165,
            "protein": 4.8,
            "fat": 1.8,
            "carb": 32,
            "fiber": 2.2,
        },
        "ingredients": [
            {
                "name": "小米",
                "amount": "60 g",
                "main": True,
            },
            {
                "name": "南瓜",
                "amount": "150 g",
                "main": True,
            },
            {
                "name": "清水",
                "amount": "700 ml",
            },
        ],
        "steps": [
            {
                "title": "小米淘洗",
                "desc": "小米轻搓两遍淘净，避免用力搓掉表层营养。",
                "minutes": 2,
            },
            {
                "title": "南瓜切块",
                "desc": "南瓜去皮切 2 cm 小块，越小越易出沙。",
                "minutes": 4,
            },
            {
                "title": "同煮出沙",
                "desc": "水开下小米与南瓜，转小火煮 18 分钟，其间搅拌两三次。",
                "minutes": 18,
            },
            {
                "title": "压泥增稠",
                "desc": "用勺背轻压南瓜块，再煮 2 分钟至粥体粘稠即可。",
                "minutes": 2,
            },
        ],
        "tips": "水开再下米不易糊底；砂锅或不粘锅效果最好。",
    },
    "tofu-soup": {
        "name": "番茄豆腐汤",
        "subtitle": "清爽开胃 · 15 分钟",
        "desc": "番茄先炒出沙，再加开水成汤，最后下豆腐与蛋液。",
        "cover": "linear-gradient(135deg, #ffb199 0%, #ff4b2b 100%)",
        "emoji": "🍅",
        "time": 15,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["soup", "light", "quick"],
        "nutrition": {
            "calorie": 120,
            "protein": 9,
            "fat": 5.5,
            "carb": 8,
            "fiber": 1.6,
        },
        "ingredients": [
            {
                "name": "嫩豆腐",
                "amount": "1 盒",
                "main": True,
            },
            {
                "name": "番茄",
                "amount": "2 个",
                "main": True,
            },
            {
                "name": "鸡蛋",
                "amount": "1 个",
            },
            {
                "name": "葱花",
                "amount": "适量",
            },
        ],
        "steps": [
            {
                "title": "炒出番茄沙",
                "desc": "番茄去皮切块，热油中火炒 3 分钟至软烂出汁。",
                "minutes": 4,
            },
            {
                "title": "加汤煮豆腐",
                "desc": "加 600 ml 开水，沸后下豆腐小块煮 3 分钟。",
                "minutes": 4,
            },
            {
                "title": "淋蛋液调味",
                "desc": "转小火淋入蛋液，停 10 秒再轻推成蛋花，加盐葱花出锅。",
                "minutes": 2,
            },
        ],
        "tips": "番茄顶部划十字用开水烫 20 秒，去皮很轻松。",
    },
    "chicken-soup": {
        "name": "菌菇鸡汤",
        "subtitle": "清甜醇香 · 慢炖 90 分钟",
        "desc": "鸡块焯透后与干菌菇同炖，菌菇提前泡发，泡菇水不浪费。",
        "cover": "linear-gradient(135deg, #f5e6b8 0%, #b08d57 100%)",
        "emoji": "🍲",
        "time": 90,
        "difficulty": "简单",
        "serving": "3 人份",
        "tags": ["soup", "warming"],
        "nutrition": {
            "calorie": 185,
            "protein": 19,
            "fat": 9,
            "carb": 6,
            "fiber": 1.5,
        },
        "ingredients": [
            {
                "name": "三黄鸡",
                "amount": "半只",
                "main": True,
            },
            {
                "name": "干香菇 / 茶树菇",
                "amount": "各 20 g",
                "main": True,
            },
            {
                "name": "红枣",
                "amount": "5 颗",
            },
            {
                "name": "姜片",
                "amount": "4 片",
            },
            {
                "name": "盐",
                "amount": "4 g",
            },
        ],
        "steps": [
            {
                "title": "泡发菌菇",
                "desc": "干菌菇用温水泡 20 分钟，泡菇水留着一起入锅。",
                "minutes": 20,
            },
            {
                "title": "鸡肉焯水",
                "desc": "鸡块冷水下锅，加姜片与料酒，沸后撇沫煮 3 分钟捞出。",
                "minutes": 6,
            },
            {
                "title": "小火慢炖",
                "desc": "鸡块、菌菇、红枣加 1.5 L 水，大火烧开转小火炖 70 分钟。",
                "minutes": 70,
            },
            {
                "title": "调味定咸",
                "desc": "出锅前 5 分钟加盐，撒葱花即可。",
                "minutes": 5,
            },
        ],
        "tips": "盐一定最后加，过早加盐会让鸡肉蛋白质收缩、汤味变淡。",
    },
    "winter-melon-soup": {
        "name": "冬瓜排骨汤",
        "subtitle": "清润解腻 · 汤清味鲜",
        "desc": "排骨冷水焯透，冬瓜后放保形，全程保持微沸避免汤浑。",
        "cover": "linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%)",
        "emoji": "🥣",
        "time": 60,
        "difficulty": "简单",
        "serving": "3 人份",
        "tags": ["soup", "light"],
        "nutrition": {
            "calorie": 150,
            "protein": 14,
            "fat": 8,
            "carb": 6,
            "fiber": 1.2,
        },
        "ingredients": [
            {
                "name": "猪肋排",
                "amount": "400 g",
                "main": True,
            },
            {
                "name": "冬瓜",
                "amount": "400 g",
                "main": True,
            },
            {
                "name": "姜片",
                "amount": "3 片",
            },
            {
                "name": "枸杞",
                "amount": "10 粒",
            },
        ],
        "steps": [
            {
                "title": "排骨焯洗",
                "desc": "排骨冷水下锅，加姜片料酒，沸后煮 3 分钟，捞出用温水冲净浮沫。",
                "minutes": 6,
            },
            {
                "title": "炖出清汤",
                "desc": "排骨加 1.2 L 开水与姜片，保持微沸炖 40 分钟。",
                "minutes": 40,
            },
            {
                "title": "下冬瓜",
                "desc": "冬瓜去皮切厚片，入锅煮 12 分钟至半透明。",
                "minutes": 12,
            },
            {
                "title": "调味",
                "desc": "加盐与枸杞，煮 2 分钟关火。",
                "minutes": 2,
            },
        ],
        "tips": "冬瓜皮别急着扔，洗净同煮 10 分钟再捞出，清热效果更好。",
    },
    "boiled-egg": {
        "name": "溏心水煮蛋",
        "subtitle": "蛋黄流心 · 8 分钟定点",
        "desc": "冷水下锅、沸后计时 6 分半，捞出立刻冰水，蛋白凝固而蛋黄微溏。",
        "cover": "linear-gradient(135deg, #fff6d5 0%, #e8b93f 100%)",
        "emoji": "🥚",
        "time": 8,
        "difficulty": "简单",
        "serving": "1 人份",
        "tags": ["light", "quick", "staple"],
        "nutrition": {
            "calorie": 78,
            "protein": 6.8,
            "fat": 5.2,
            "carb": 0.6,
            "fiber": 0,
        },
        "ingredients": [
            {
                "name": "鸡蛋",
                "amount": "1 个",
                "main": True,
            },
            {
                "name": "盐",
                "amount": "1 小勺",
            },
            {
                "name": "冰水",
                "amount": "1 盆",
            },
        ],
        "steps": [
            {
                "title": "常温回温",
                "desc": "冷藏蛋提前取出回温 5 分钟，避免入锅爆裂。",
                "minutes": 5,
            },
            {
                "title": "冷水下锅",
                "desc": "水没过蛋，加一小勺盐，中火加热至沸。",
                "minutes": 2,
            },
            {
                "title": "精准计时",
                "desc": "水沸后转中小火计时 6 分 30 秒，即得溏心。",
                "minutes": 7,
            },
            {
                "title": "冰水定心",
                "desc": "立刻捞出放入冰水 2 分钟，剥壳完整、蛋黄不回熟。",
                "minutes": 2,
            },
        ],
        "tips": "想要全熟蛋沸后煮 9 分钟；水里加盐能让破壳时蛋白不外溢。",
    },
    "rice": {
        "name": "杂粮米饭",
        "subtitle": "三种谷物 · 低升糖",
        "desc": "大米配糙米与小米，提前浸泡让口感更软糯，膳食纤维明显提升。",
        "cover": "linear-gradient(135deg, #f7f1e3 0%, #b99668 100%)",
        "emoji": "🍚",
        "time": 30,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["staple", "light"],
        "nutrition": {
            "calorie": 210,
            "protein": 5.2,
            "fat": 0.9,
            "carb": 45,
            "fiber": 2.4,
        },
        "ingredients": [
            {
                "name": "大米",
                "amount": "120 g",
                "main": True,
            },
            {
                "name": "糙米",
                "amount": "40 g",
                "main": True,
            },
            {
                "name": "小米",
                "amount": "20 g",
            },
            {
                "name": "清水",
                "amount": "约 260 ml",
            },
        ],
        "steps": [
            {
                "title": "淘洗浸泡",
                "desc": "三种米混合淘洗两遍，加水浸泡 20 分钟。",
                "minutes": 20,
            },
            {
                "title": "按比例加水",
                "desc": "水面高出米约 1.2 cm，糙米吸水多，比纯白米多加点水。",
                "minutes": 1,
            },
            {
                "title": "焖煮",
                "desc": "电饭煲标准煮饭模式，煮好后再焖 5 分钟。",
                "minutes": 20,
            },
            {
                "title": "翻松",
                "desc": "开盖用饭勺翻松，散掉多余水汽。",
                "minutes": 1,
            },
        ],
        "tips": "糙米难熟，可用温水浸泡，或前一晚冷藏浸泡。",
    },
    "soy-milk": {
        "name": "现磨豆浆",
        "subtitle": "豆香浓郁 · 无渣版",
        "desc": "黄豆泡发后打浆，煮浆必须沸腾后再小火滚 5 分钟，彻底破坏皂苷。",
        "cover": "linear-gradient(135deg, #fdfbf3 0%, #cdbb92 100%)",
        "emoji": "🥛",
        "time": 15,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["light", "quick"],
        "nutrition": {
            "calorie": 95,
            "protein": 7.6,
            "fat": 4.4,
            "carb": 6.2,
            "fiber": 1.6,
        },
        "ingredients": [
            {
                "name": "干黄豆",
                "amount": "50 g",
                "main": True,
            },
            {
                "name": "清水",
                "amount": "700 ml",
                "main": True,
            },
        ],
        "steps": [
            {
                "title": "浸泡黄豆",
                "desc": "黄豆冷水浸泡 6 小时以上至完全膨发。",
                "minutes": 5,
            },
            {
                "title": "加水打浆",
                "desc": "豆水按 1:14 入破壁机，高速打 2 分钟。",
                "minutes": 2,
            },
            {
                "title": "滤渣",
                "desc": "用滤网或纱布滤去豆渣，口感更顺滑。",
                "minutes": 3,
            },
            {
                "title": "煮沸去腥",
                "desc": "生浆边搅边煮，沸腾后转小火再滚 5 分钟去豆腥。",
                "minutes": 8,
            },
        ],
        "tips": "豆浆会出现\"假沸\"，沫子涌起就以为熟了，必须再多煮 5 分钟才安全。",
    },
    "scallion-pancake": {
        "name": "葱油饼",
        "subtitle": "层层起酥 · 20 分钟",
        "desc": "烫面加凉面揉成半烫面，抹油酥卷起再擀，层次更分明。",
        "cover": "linear-gradient(135deg, #ffe9b8 0%, #cf9a30 100%)",
        "emoji": "🥞",
        "time": 20,
        "difficulty": "中等",
        "serving": "2 人份",
        "tags": ["staple", "quick"],
        "nutrition": {
            "calorie": 265,
            "protein": 6.4,
            "fat": 11,
            "carb": 35,
            "fiber": 1.4,
        },
        "ingredients": [
            {
                "name": "中筋面粉",
                "amount": "200 g",
                "main": True,
            },
            {
                "name": "小葱",
                "amount": "1 把",
                "main": True,
            },
            {
                "name": "开水 / 凉水",
                "amount": "各 60 ml",
            },
            {
                "name": "食用油",
                "amount": "2 勺",
            },
            {
                "name": "盐",
                "amount": "2 g",
            },
        ],
        "steps": [
            {
                "title": "半烫面",
                "desc": "面粉先用开水烫一半，再加凉水揉成光滑面团，醒 10 分钟。",
                "minutes": 12,
            },
            {
                "title": "调油酥",
                "desc": "两勺面粉加热油调成流动油酥，加盐拌匀。",
                "minutes": 2,
            },
            {
                "title": "卷起擀开",
                "desc": "面团擀薄抹油酥撒葱花，卷成螺旋后压扁再擀成饼。",
                "minutes": 4,
            },
            {
                "title": "小火煎香",
                "desc": "锅中小火少油，两面各煎 2 分钟至金黄起层。",
                "minutes": 4,
            },
        ],
        "tips": "油酥是起层的关键，抹足但别抹到边缘，否则卷的时候会漏。",
    },
    "vinegar-cabbage": {
        "name": "醋溜白菜",
        "subtitle": "酸香脆口 · 8 分钟",
        "desc": "白菜帮先下锅、叶子后放，醋分两次沿锅边烹入，酸味更立体。",
        "cover": "linear-gradient(135deg, #f0f7dd 0%, #7fa93f 100%)",
        "emoji": "🥬",
        "time": 8,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["veg", "light", "quick"],
        "nutrition": {
            "calorie": 82,
            "protein": 2.4,
            "fat": 4.6,
            "carb": 8.2,
            "fiber": 2.6,
        },
        "ingredients": [
            {
                "name": "大白菜",
                "amount": "半颗",
                "main": True,
            },
            {
                "name": "干辣椒",
                "amount": "2 个",
            },
            {
                "name": "陈醋",
                "amount": "2 勺",
                "main": True,
            },
            {
                "name": "蒜片",
                "amount": "3 片",
            },
        ],
        "steps": [
            {
                "title": "分刀处理",
                "desc": "白菜帮斜刀片薄，叶子手撕成大块分开装。",
                "minutes": 3,
            },
            {
                "title": "爆香干料",
                "desc": "热油下干辣椒与蒜片，小火煸出香味。",
                "minutes": 1,
            },
            {
                "title": "先炒菜帮",
                "desc": "下白菜帮大火翻炒 2 分钟至边缘透明。",
                "minutes": 2,
            },
            {
                "title": "下叶烹醋",
                "desc": "加菜叶炒软，沿锅边烹入陈醋，起锅前再补半勺。",
                "minutes": 2,
            },
        ],
        "tips": "醋要沿热锅边淋入，高温激发香气；分两次放酸味层次更足。",
    },
    "cucumber-salad": {
        "name": "拍黄瓜",
        "subtitle": "爽脆开胃 · 6 分钟",
        "desc": "黄瓜拍裂而不是切片，断面粗糙更挂汁，蒜末现砸才够香。",
        "cover": "linear-gradient(135deg, #e7f7e1 0%, #5aa843 100%)",
        "emoji": "🥒",
        "time": 6,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["veg", "light", "quick"],
        "nutrition": {
            "calorie": 45,
            "protein": 1.2,
            "fat": 2.8,
            "carb": 4,
            "fiber": 1.1,
        },
        "ingredients": [
            {
                "name": "黄瓜",
                "amount": "2 根",
                "main": True,
            },
            {
                "name": "大蒜",
                "amount": "3 瓣",
                "main": True,
            },
            {
                "name": "香醋 / 生抽",
                "amount": "各 1 勺",
            },
            {
                "name": "香油",
                "amount": "半勺",
            },
        ],
        "steps": [
            {
                "title": "拍裂切段",
                "desc": "黄瓜用刀面拍裂至自然断开，再切 4 cm 段。",
                "minutes": 2,
            },
            {
                "title": "盐渍出水",
                "desc": "撒盐腌 3 分钟，倒掉渗出的水，口感更脆。",
                "minutes": 3,
            },
            {
                "title": "调味拌匀",
                "desc": "蒜末、醋、生抽、香油拌匀浇上，静置 2 分钟入味。",
                "minutes": 2,
            },
        ],
        "tips": "拍比切好：拍出的粗糙断面更容易挂味。",
    },
    "steamed-bun": {
        "name": "香菇青菜包",
        "subtitle": "素馅鲜香 · 45 分钟",
        "desc": "青菜焯水挤干切碎，与香菇末拌馅，包好二次醒发 15 分钟再蒸。",
        "cover": "linear-gradient(135deg, #f6f7ec 0%, #a4b06a 100%)",
        "emoji": "🥟",
        "time": 45,
        "difficulty": "中等",
        "serving": "约 10 个",
        "tags": ["staple", "veg"],
        "nutrition": {
            "calorie": 190,
            "protein": 5.8,
            "fat": 4.2,
            "carb": 32,
            "fiber": 2.8,
        },
        "ingredients": [
            {
                "name": "中筋面粉",
                "amount": "300 g",
                "main": True,
            },
            {
                "name": "小青菜",
                "amount": "400 g",
                "main": True,
            },
            {
                "name": "干香菇",
                "amount": "6 朵",
            },
            {
                "name": "酵母",
                "amount": "3 g",
            },
            {
                "name": "香油",
                "amount": "1 勺",
            },
        ],
        "steps": [
            {
                "title": "和面发酵",
                "desc": "酵母用温水化开，加面粉揉成面团，温暖处发酵至两倍大。",
                "minutes": 25,
            },
            {
                "title": "处理馅料",
                "desc": "青菜焯水 30 秒过凉挤干切碎，香菇泡发切末，混合调味。",
                "minutes": 8,
            },
            {
                "title": "包制",
                "desc": "面团排气分剂，擀成中间厚边缘薄的圆皮包馅。",
                "minutes": 10,
            },
            {
                "title": "二发蒸制",
                "desc": "包好醒发 15 分钟，水开后中火蒸 12 分钟，关火焖 3 分钟。",
                "minutes": 15,
            },
        ],
        "tips": "青菜一定要挤干水，否则蒸出来包子底会塌陷。",
    },
    "stir-greens": {
        "name": "蚝油生菜",
        "subtitle": "脆嫩碧绿 · 6 分钟",
        "desc": "生菜焯水 20 秒立刻捞出，另起锅做蚝油汁淋上，比直接炒更翠绿。",
        "cover": "linear-gradient(135deg, #e9f9e4 0%, #4c9a3f 100%)",
        "emoji": "🥬",
        "time": 6,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["veg", "light", "quick"],
        "nutrition": {
            "calorie": 68,
            "protein": 1.8,
            "fat": 4.2,
            "carb": 5.6,
            "fiber": 1.4,
        },
        "ingredients": [
            {
                "name": "球生菜",
                "amount": "1 颗",
                "main": True,
            },
            {
                "name": "蚝油",
                "amount": "2 勺",
                "main": True,
            },
            {
                "name": "蒜末",
                "amount": "1 勺",
            },
            {
                "name": "水淀粉",
                "amount": "2 勺",
            },
        ],
        "steps": [
            {
                "title": "焯水定色",
                "desc": "水开加少许油盐，生菜下锅 20 秒捞出摆盘。",
                "minutes": 2,
            },
            {
                "title": "调蚝油汁",
                "desc": "少油炒香蒜末，加蚝油、两勺水，用水淀粉勾薄芡。",
                "minutes": 2,
            },
            {
                "title": "浇汁",
                "desc": "趁热把汁均匀淋在生菜上即可。",
                "minutes": 1,
            },
        ],
        "tips": "焯水时间超过 30 秒生菜就会软塌，宁可短不要长。",
    },
    "cold-noodle": {
        "name": "麻酱凉面",
        "subtitle": "芝麻香浓 · 15 分钟",
        "desc": "麻酱先用温水澥开再加酱油醋，面条过冷水后拌少许油防粘。",
        "cover": "linear-gradient(135deg, #fbe9cf 0%, #c08a4a 100%)",
        "emoji": "🍜",
        "time": 15,
        "difficulty": "简单",
        "serving": "1 人份",
        "tags": ["staple", "quick"],
        "nutrition": {
            "calorie": 390,
            "protein": 11,
            "fat": 15,
            "carb": 52,
            "fiber": 2.2,
        },
        "ingredients": [
            {
                "name": "面条",
                "amount": "150 g",
                "main": True,
            },
            {
                "name": "芝麻酱",
                "amount": "2 勺",
                "main": True,
            },
            {
                "name": "黄瓜丝",
                "amount": "半根",
            },
            {
                "name": "生抽 / 香醋",
                "amount": "各 1 勺",
            },
            {
                "name": "芝麻油",
                "amount": "1 勺",
            },
        ],
        "steps": [
            {
                "title": "澥麻酱",
                "desc": "芝麻酱分次加温水，同一方向搅至顺滑流动。",
                "minutes": 3,
            },
            {
                "title": "煮面过凉",
                "desc": "面条煮至八成熟捞出，过两遍冷水，沥干拌少许油。",
                "minutes": 5,
            },
            {
                "title": "调味拌匀",
                "desc": "麻酱加生抽、醋、糖、蒜水调匀，与面拌匀。",
                "minutes": 2,
            },
            {
                "title": "配菜装盘",
                "desc": "铺黄瓜丝，撒花生碎与香菜。",
                "minutes": 1,
            },
        ],
        "tips": "麻酱不能一次加太多水，会成疙瘩；少量多次才能澥开。",
    },
    "egg-custard": {
        "name": "虾仁蒸蛋",
        "subtitle": "嫩滑无孔 · 12 分钟",
        "desc": "蛋液与温水 1:1.5 混合过筛，盖保鲜膜中小火蒸，表面平滑如镜。",
        "cover": "linear-gradient(135deg, #fff3d6 0%, #e8a93f 100%)",
        "emoji": "🥚",
        "time": 12,
        "difficulty": "简单",
        "serving": "1 人份",
        "tags": ["light", "quick"],
        "nutrition": {
            "calorie": 145,
            "protein": 14,
            "fat": 8,
            "carb": 3,
            "fiber": 0.2,
        },
        "ingredients": [
            {
                "name": "鸡蛋",
                "amount": "2 个",
                "main": True,
            },
            {
                "name": "虾仁",
                "amount": "6 只",
                "main": True,
            },
            {
                "name": "温水",
                "amount": "约 150 ml",
            },
            {
                "name": "生抽 / 香油",
                "amount": "各少许",
            },
        ],
        "steps": [
            {
                "title": "调蛋液",
                "desc": "蛋液加 1.5 倍温水与少许盐，同方向搅匀后过筛去泡。",
                "minutes": 3,
            },
            {
                "title": "盖膜蒸制",
                "desc": "碗口盖保鲜膜扎小孔，水开后中小火蒸 8 分钟。",
                "minutes": 8,
            },
            {
                "title": "放虾再蒸",
                "desc": "摆上腌好的虾仁，再蒸 3 分钟至变色。",
                "minutes": 3,
            },
            {
                "title": "调味",
                "desc": "淋少许生抽与香油，撒葱花。",
                "minutes": 1,
            },
        ],
        "tips": "必须用温水且蛋液过筛；火太大蛋羹会起蜂窝。",
    },
    "whole-wheat-toast": {
        "name": "全麦吐司",
        "subtitle": "低糖配方 · 5 分钟",
        "desc": "现成全麦吐司复烤 3 分钟即可，表面微焦才有麦香。",
        "cover": "linear-gradient(135deg, #f7e8d0 0%, #b07a42 100%)",
        "emoji": "🍞",
        "time": 5,
        "difficulty": "简单",
        "serving": "1 人份",
        "tags": ["staple", "light", "quick"],
        "nutrition": {
            "calorie": 160,
            "protein": 6.2,
            "fat": 2.4,
            "carb": 29,
            "fiber": 3.4,
        },
        "ingredients": [
            {
                "name": "全麦吐司",
                "amount": "2 片",
                "main": True,
            },
            {
                "name": "黄油",
                "amount": "5 g",
            },
            {
                "name": "蜂蜜",
                "amount": "少许",
            },
        ],
        "steps": [
            {
                "title": "复烤",
                "desc": "吐司放入烤箱或平底锅，180°C 烤 3 分钟至边缘微焦。",
                "minutes": 3,
            },
            {
                "title": "抹酱",
                "desc": "趁热抹薄薄一层黄油，淋少许蜂蜜。",
                "minutes": 1,
            },
        ],
        "tips": "选配料表里\"全麦粉\"排第一位的产品，才是真全麦。",
    },
    "pepper-pork": {
        "name": "青椒炒肉丝",
        "subtitle": "家常下饭 · 15 分钟",
        "desc": "肉丝上浆后滑炒再盛出，青椒单独断生，最后合炒保持各自口感。",
        "cover": "linear-gradient(135deg, #e6f3c9 0%, #6f9e35 100%)",
        "emoji": "🌶️",
        "time": 15,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["meat", "quick"],
        "nutrition": {
            "calorie": 295,
            "protein": 22,
            "fat": 19,
            "carb": 8,
            "fiber": 1.8,
        },
        "ingredients": [
            {
                "name": "猪里脊",
                "amount": "250 g",
                "main": True,
            },
            {
                "name": "青椒",
                "amount": "2 个",
                "main": True,
            },
            {
                "name": "生抽 / 料酒",
                "amount": "各 1 勺",
            },
            {
                "name": "淀粉",
                "amount": "1 勺",
            },
        ],
        "steps": [
            {
                "title": "切丝上浆",
                "desc": "里脊顺纹切细丝，加生抽、料酒、淀粉抓匀腌 10 分钟。",
                "minutes": 10,
            },
            {
                "title": "滑炒肉丝",
                "desc": "热锅凉油下肉丝快速划散，变色盛出。",
                "minutes": 3,
            },
            {
                "title": "煸青椒",
                "desc": "底油下青椒丝大火煸 1 分钟至表皮起虎皮。",
                "minutes": 2,
            },
            {
                "title": "合炒调味",
                "desc": "倒回肉丝，加盐与少许生抽快速炒匀出锅。",
                "minutes": 2,
            },
        ],
        "tips": "肉丝顺纹切不散，逆纹切更嫩，家常炒丝建议逆纹。",
    },
    "spinach-vermicelli": {
        "name": "菠菜粉丝",
        "subtitle": "清爽凉拌 · 10 分钟",
        "desc": "菠菜焯水去草酸，粉丝泡软后过凉水，蒜香调味最解腻。",
        "cover": "linear-gradient(135deg, #e4f5e6 0%, #3f8f5a 100%)",
        "emoji": "🥬",
        "time": 10,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["veg", "light", "quick"],
        "nutrition": {
            "calorie": 110,
            "protein": 3.6,
            "fat": 3.8,
            "carb": 16,
            "fiber": 2.2,
        },
        "ingredients": [
            {
                "name": "菠菜",
                "amount": "300 g",
                "main": True,
            },
            {
                "name": "粉丝",
                "amount": "1 把",
                "main": True,
            },
            {
                "name": "蒜末",
                "amount": "1 勺",
            },
            {
                "name": "香醋 / 生抽",
                "amount": "各 1 勺",
            },
        ],
        "steps": [
            {
                "title": "泡发粉丝",
                "desc": "粉丝温水泡 8 分钟至软，剪短备用。",
                "minutes": 8,
            },
            {
                "title": "焯菠菜",
                "desc": "水开下菠菜焯 40 秒，捞出过凉挤干水分。",
                "minutes": 2,
            },
            {
                "title": "拌制",
                "desc": "菠菜、粉丝加蒜末、醋、生抽、香油拌匀。",
                "minutes": 2,
            },
        ],
        "tips": "菠菜焯水能去掉大部分草酸，口感不涩也更利于钙吸收。",
    },
    "red-bean-soup": {
        "name": "红枣红豆汤",
        "subtitle": "甜润暖身 · 40 分钟",
        "desc": "红豆提前浸泡，与红枣同煮至开花，最后加冰糖再煮 5 分钟。",
        "cover": "linear-gradient(135deg, #fbe0e0 0%, #a33a3a 100%)",
        "emoji": "🥣",
        "time": 40,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["light", "warming"],
        "nutrition": {
            "calorie": 180,
            "protein": 7.8,
            "fat": 0.6,
            "carb": 36,
            "fiber": 5.2,
        },
        "ingredients": [
            {
                "name": "红豆",
                "amount": "100 g",
                "main": True,
            },
            {
                "name": "红枣",
                "amount": "6 颗",
                "main": True,
            },
            {
                "name": "冰糖",
                "amount": "15 g",
            },
            {
                "name": "清水",
                "amount": "1 L",
            },
        ],
        "steps": [
            {
                "title": "浸泡红豆",
                "desc": "红豆冷水浸泡 2 小时以上，煮时更易开花。",
                "minutes": 5,
            },
            {
                "title": "同煮",
                "desc": "红豆与红枣加水大火烧开，转小火煮 35 分钟。",
                "minutes": 35,
            },
            {
                "title": "加糖收尾",
                "desc": "红豆开花后加冰糖，再煮 5 分钟至融化。",
                "minutes": 5,
            },
        ],
        "tips": "糖一定要最后加，过早加糖红豆不容易煮烂。",
    },
    "tea-egg": {
        "name": "五香茶叶蛋",
        "subtitle": "入味弹嫩 · 50 分钟",
        "desc": "蛋煮至全熟后敲出裂纹，卤汁浸泡越久越入味，隔夜最佳。",
        "cover": "linear-gradient(135deg, #f0e2cf 0%, #8a5a2b 100%)",
        "emoji": "🥚",
        "time": 50,
        "difficulty": "简单",
        "serving": "4 个",
        "tags": ["light"],
        "nutrition": {
            "calorie": 82,
            "protein": 6.8,
            "fat": 5.2,
            "carb": 1.4,
            "fiber": 0,
        },
        "ingredients": [
            {
                "name": "鸡蛋",
                "amount": "4 个",
                "main": True,
            },
            {
                "name": "红茶包",
                "amount": "2 个",
                "main": True,
            },
            {
                "name": "八角 / 桂皮 / 香叶",
                "amount": "各适量",
            },
            {
                "name": "生抽",
                "amount": "3 勺",
            },
            {
                "name": "冰糖",
                "amount": "10 g",
            },
        ],
        "steps": [
            {
                "title": "煮蛋敲纹",
                "desc": "蛋冷水下锅煮 9 分钟，捞出用勺背轻敲出裂纹。",
                "minutes": 10,
            },
            {
                "title": "调卤汁",
                "desc": "另起锅加水、红茶、香料、生抽与冰糖煮开。",
                "minutes": 5,
            },
            {
                "title": "卤制",
                "desc": "放入鸡蛋小火卤 30 分钟，关火浸泡至凉。",
                "minutes": 30,
            },
        ],
        "tips": "冷藏浸泡一夜风味最佳；裂纹越均匀，花纹越漂亮。",
    },
    "sweet-sour-ribs": {
        "name": "糖醋小排",
        "subtitle": "酸甜挂汁 · 45 分钟",
        "desc": "排骨先煎后焖，糖醋汁按 1:2:3 比例调好，收汁阶段不停翻动防糊。",
        "cover": "linear-gradient(135deg, #fbc7a4 0%, #c2410c 100%)",
        "emoji": "🍖",
        "time": 45,
        "difficulty": "中等",
        "serving": "2 人份",
        "tags": ["meat", "warming"],
        "nutrition": {
            "calorie": 420,
            "protein": 24,
            "fat": 28,
            "carb": 18,
            "fiber": 0.6,
        },
        "ingredients": [
            {
                "name": "猪小排",
                "amount": "500 g",
                "main": True,
            },
            {
                "name": "冰糖",
                "amount": "20 g",
                "main": True,
            },
            {
                "name": "香醋",
                "amount": "3 勺",
            },
            {
                "name": "生抽 / 料酒",
                "amount": "各 1 勺",
            },
            {
                "name": "姜片",
                "amount": "3 片",
            },
        ],
        "steps": [
            {
                "title": "焯水",
                "desc": "小排冷水下锅，加姜片料酒，沸后煮 3 分钟捞出洗净。",
                "minutes": 5,
            },
            {
                "title": "煎至微焦",
                "desc": "锅中少油，小排中火煎至表面金黄。",
                "minutes": 7,
            },
            {
                "title": "调汁焖煮",
                "desc": "加冰糖、醋、生抽与开水，小火焖 25 分钟。",
                "minutes": 25,
            },
            {
                "title": "收汁挂味",
                "desc": "大火收汁，不断翻动让糖醋汁均匀裹上。",
                "minutes": 5,
            },
        ],
        "tips": "收汁时糖分高易糊，宁可早关火，用余温继续裹汁。",
    },
    "oil-bean-sprouts": {
        "name": "炝炒豆芽",
        "subtitle": "爽脆微辣 · 7 分钟",
        "desc": "豆芽大火快炒，全程不超过 3 分钟，出锅前淋醋保持脆度。",
        "cover": "linear-gradient(135deg, #f4f7dc 0%, #7d9e3f 100%)",
        "emoji": "🌱",
        "time": 7,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["veg", "quick", "spicy"],
        "nutrition": {
            "calorie": 75,
            "protein": 3.2,
            "fat": 4,
            "carb": 7,
            "fiber": 1.8,
        },
        "ingredients": [
            {
                "name": "绿豆芽",
                "amount": "400 g",
                "main": True,
            },
            {
                "name": "干辣椒",
                "amount": "3 个",
                "main": True,
            },
            {
                "name": "花椒",
                "amount": "10 粒",
            },
            {
                "name": "香醋",
                "amount": "1 勺",
            },
        ],
        "steps": [
            {
                "title": "摘洗",
                "desc": "豆芽掐去须根，冲洗沥干，水分越少越好炒。",
                "minutes": 3,
            },
            {
                "title": "炝锅",
                "desc": "热油下花椒与干辣椒，小火煸出麻香后捞出。",
                "minutes": 1,
            },
            {
                "title": "猛火快炒",
                "desc": "下豆芽大火翻炒 2 分钟，加盐，起锅前淋醋。",
                "minutes": 3,
            },
        ],
        "tips": "豆芽带水下锅会出汤，提前沥干或用厨房纸吸干。",
    },
    "seaweed-egg-soup": {
        "name": "紫菜蛋花汤",
        "subtitle": "3 分钟快手汤",
        "desc": "水开后关小火再淋蛋液，蛋花才细嫩成片不结块。",
        "cover": "linear-gradient(135deg, #e6f0f7 0%, #2f7fc1 100%)",
        "emoji": "🍲",
        "time": 8,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["soup", "light", "quick"],
        "nutrition": {
            "calorie": 78,
            "protein": 6.4,
            "fat": 4.2,
            "carb": 3.6,
            "fiber": 0.8,
        },
        "ingredients": [
            {
                "name": "干紫菜",
                "amount": "10 g",
                "main": True,
            },
            {
                "name": "鸡蛋",
                "amount": "1 个",
                "main": True,
            },
            {
                "name": "虾皮",
                "amount": "1 小把",
            },
            {
                "name": "香油 / 白胡椒",
                "amount": "少许",
            },
        ],
        "steps": [
            {
                "title": "泡发紫菜",
                "desc": "紫菜温水冲洗两遍，去除杂质与沙粒。",
                "minutes": 2,
            },
            {
                "title": "煮汤底",
                "desc": "水开加虾皮煮 2 分钟提鲜。",
                "minutes": 2,
            },
            {
                "title": "淋蛋花",
                "desc": "转最小火，蛋液细流淋入，静置 10 秒再轻推。",
                "minutes": 2,
            },
            {
                "title": "调味",
                "desc": "加紫菜、盐、白胡椒与香油即可。",
                "minutes": 1,
            },
        ],
        "tips": "紫菜最后放，久煮会发苦。",
    },
    "pancake-fruit": {
        "name": "酸奶松饼",
        "subtitle": "松软微甜 · 20 分钟",
        "desc": "酸奶调糊无需打发，平底锅小火单面煎至起泡再翻面。",
        "cover": "linear-gradient(135deg, #ffe4b8 0%, #cf8a2c 100%)",
        "emoji": "🥞",
        "time": 20,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["staple"],
        "nutrition": {
            "calorie": 285,
            "protein": 9.6,
            "fat": 8.4,
            "carb": 42,
            "fiber": 1.8,
        },
        "ingredients": [
            {
                "name": "低筋面粉",
                "amount": "120 g",
                "main": True,
            },
            {
                "name": "原味酸奶",
                "amount": "120 g",
                "main": True,
            },
            {
                "name": "鸡蛋",
                "amount": "1 个",
            },
            {
                "name": "泡打粉",
                "amount": "3 g",
            },
            {
                "name": "蜂蜜",
                "amount": "少许",
            },
        ],
        "steps": [
            {
                "title": "调糊",
                "desc": "酸奶、鸡蛋拌匀，筛入面粉与泡打粉，搅至无干粉即可，别过度搅拌。",
                "minutes": 4,
            },
            {
                "title": "静置",
                "desc": "面糊静置 5 分钟让泡打粉作用，饼更蓬松。",
                "minutes": 5,
            },
            {
                "title": "小火煎制",
                "desc": "不粘锅小火，舀一勺面糊，冒泡后翻面再煎 1 分钟。",
                "minutes": 8,
            },
            {
                "title": "装盘",
                "desc": "叠放淋蜂蜜，搭配水果。",
                "minutes": 2,
            },
        ],
        "tips": "全程小火，否则外焦内不熟；面糊起大泡就是翻面时机。",
    },
    "fruit-plate": {
        "name": "时令水果拼盘",
        "subtitle": "五种配色 · 5 分钟",
        "desc": "选当季水果，按颜色搭配摆盘，视觉与营养都更均衡。",
        "cover": "linear-gradient(135deg, #ffe0d6 0%, #e0654a 100%)",
        "emoji": "🍎",
        "time": 5,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["light", "quick"],
        "nutrition": {
            "calorie": 110,
            "protein": 1.4,
            "fat": 0.4,
            "carb": 26,
            "fiber": 3.2,
        },
        "ingredients": [
            {
                "name": "苹果",
                "amount": "1 个",
                "main": True,
            },
            {
                "name": "圣女果",
                "amount": "8 颗",
                "main": True,
            },
            {
                "name": "蓝莓",
                "amount": "1 小把",
            },
            {
                "name": "香蕉",
                "amount": "1 根",
            },
        ],
        "steps": [
            {
                "title": "清洗",
                "desc": "水果逐一冲洗，蓝莓用淡盐水泡 2 分钟后冲净。",
                "minutes": 3,
            },
            {
                "title": "切配摆盘",
                "desc": "苹果切块、香蕉切片，按颜色分区摆放。",
                "minutes": 2,
            },
        ],
        "tips": "苹果切好后泡 30 秒淡盐水，可防止氧化变黑。",
    },
    "braised-chicken": {
        "name": "香菇滑鸡",
        "subtitle": "嫩滑多汁 · 30 分钟",
        "desc": "鸡腿肉去骨切块，加香菇与蚝油焖至收汁，淀粉水让汤汁更稠滑。",
        "cover": "linear-gradient(135deg, #f3e2c7 0%, #a0522d 100%)",
        "emoji": "🍗",
        "time": 30,
        "difficulty": "中等",
        "serving": "2 人份",
        "tags": ["meat", "warming"],
        "nutrition": {
            "calorie": 305,
            "protein": 27,
            "fat": 17,
            "carb": 9,
            "fiber": 1.4,
        },
        "ingredients": [
            {
                "name": "鸡腿肉",
                "amount": "400 g",
                "main": True,
            },
            {
                "name": "干香菇",
                "amount": "6 朵",
                "main": True,
            },
            {
                "name": "蚝油 / 生抽",
                "amount": "各 1 勺",
            },
            {
                "name": "姜片 / 蒜",
                "amount": "适量",
            },
            {
                "name": "水淀粉",
                "amount": "2 勺",
            },
        ],
        "steps": [
            {
                "title": "腌制",
                "desc": "鸡腿肉切块，加生抽、淀粉、少许油抓匀腌 15 分钟。",
                "minutes": 15,
            },
            {
                "title": "泡发香菇",
                "desc": "香菇温水泡发切片，泡菇水留用。",
                "minutes": 10,
            },
            {
                "title": "焖煮",
                "desc": "爆香姜蒜，下鸡块煎至定型，加香菇与泡菇水焖 10 分钟。",
                "minutes": 12,
            },
            {
                "title": "收汁",
                "desc": "加蚝油调味，淋水淀粉勾薄芡，汤汁挂匀出锅。",
                "minutes": 3,
            },
        ],
        "tips": "泡菇水是天然的鲜味来源，过滤后代替清水焖更香。",
    },
    "lotus-root": {
        "name": "清炒藕片",
        "subtitle": "脆爽洁白 · 10 分钟",
        "desc": "藕片切好泡清水防氧化，焯水加白醋，炒出来才洁白脆口。",
        "cover": "linear-gradient(135deg, #f7f2e4 0%, #a8b06a 100%)",
        "emoji": "🥔",
        "time": 10,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["veg", "light", "quick"],
        "nutrition": {
            "calorie": 88,
            "protein": 2.4,
            "fat": 4.2,
            "carb": 11,
            "fiber": 2.6,
        },
        "ingredients": [
            {
                "name": "莲藕",
                "amount": "1 节",
                "main": True,
            },
            {
                "name": "白醋",
                "amount": "1 勺",
                "main": True,
            },
            {
                "name": "蒜片 / 干辣椒",
                "amount": "适量",
            },
        ],
        "steps": [
            {
                "title": "切片泡水",
                "desc": "藕去皮切薄片，立即泡入清水加几滴白醋。",
                "minutes": 5,
            },
            {
                "title": "焯水",
                "desc": "水开加少许白醋，藕片焯 40 秒捞出过凉。",
                "minutes": 2,
            },
            {
                "title": "快炒",
                "desc": "爆香蒜片干辣椒，下藕片大火炒 1 分钟，加盐出锅。",
                "minutes": 2,
            },
        ],
        "tips": "选七孔藕偏糯适合炖，九孔藕偏脆适合炒。",
    },
    "radish-pickle": {
        "name": "爽口萝卜丝",
        "subtitle": "酸辣开胃 · 8 分钟",
        "desc": "萝卜丝盐渍出水后挤干，拌入糖醋汁，脆度能保持很久。",
        "cover": "linear-gradient(135deg, #f0f7ec 0%, #79a85f 100%)",
        "emoji": "🥗",
        "time": 8,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["veg", "light", "quick"],
        "nutrition": {
            "calorie": 38,
            "protein": 1.1,
            "fat": 1.6,
            "carb": 5.2,
            "fiber": 1.6,
        },
        "ingredients": [
            {
                "name": "白萝卜",
                "amount": "半根",
                "main": True,
            },
            {
                "name": "小米椒",
                "amount": "2 个",
            },
            {
                "name": "白醋 / 糖",
                "amount": "各 1 勺",
            },
            {
                "name": "盐",
                "amount": "2 g",
            },
        ],
        "steps": [
            {
                "title": "切丝盐渍",
                "desc": "萝卜切细丝，加盐抓匀静置 5 分钟。",
                "minutes": 5,
            },
            {
                "title": "挤干水分",
                "desc": "用手挤掉多余水分，这是脆爽的关键。",
                "minutes": 1,
            },
            {
                "title": "拌味",
                "desc": "加糖、白醋、小米椒圈拌匀，冷藏 10 分钟更爽口。",
                "minutes": 2,
            },
        ],
        "tips": "萝卜皮附近最辣也最脆，喜欢的可以保留。",
    },
    "pumpkin-soup": {
        "name": "奶油南瓜浓汤",
        "subtitle": "绵密香甜 · 25 分钟",
        "desc": "南瓜先蒸后打泥，加牛奶与少许淡奶油，顺滑不腻。",
        "cover": "linear-gradient(135deg, #ffe9c2 0%, #cf8a2c 100%)",
        "emoji": "🎃",
        "time": 25,
        "difficulty": "简单",
        "serving": "2 人份",
        "tags": ["soup", "light"],
        "nutrition": {
            "calorie": 165,
            "protein": 5.2,
            "fat": 7.2,
            "carb": 20,
            "fiber": 2.4,
        },
        "ingredients": [
            {
                "name": "贝贝南瓜",
                "amount": "400 g",
                "main": True,
            },
            {
                "name": "牛奶",
                "amount": "200 ml",
                "main": True,
            },
            {
                "name": "淡奶油",
                "amount": "30 ml",
            },
            {
                "name": "洋葱",
                "amount": "四分之一个",
            },
        ],
        "steps": [
            {
                "title": "蒸南瓜",
                "desc": "南瓜去皮切块，上锅蒸 15 分钟至软烂。",
                "minutes": 15,
            },
            {
                "title": "炒香洋葱",
                "desc": "少油小火炒洋葱至透明出甜香。",
                "minutes": 3,
            },
            {
                "title": "打泥",
                "desc": "南瓜与洋葱加牛奶打成细腻糊状。",
                "minutes": 3,
            },
            {
                "title": "煮稠调味",
                "desc": "回锅小火煮 5 分钟，加盐与淡奶油调匀。",
                "minutes": 5,
            },
        ],
        "tips": "贝贝南瓜比普通南瓜更甜更面，可少加糖或不加。",
    },
    "veggie-sandwich": {
        "name": "蔬菜鸡蛋三明治",
        "subtitle": "早餐快手 · 8 分钟",
        "desc": "吐司先烤脆，鸡蛋煎成薄蛋皮，生菜要擦干水分避免软化面包。",
        "cover": "linear-gradient(135deg, #eef6e4 0%, #6b9e3f 100%)",
        "emoji": "🥪",
        "time": 8,
        "difficulty": "简单",
        "serving": "1 人份",
        "tags": ["staple", "light", "quick"],
        "nutrition": {
            "calorie": 275,
            "protein": 13,
            "fat": 11,
            "carb": 30,
            "fiber": 2.6,
        },
        "ingredients": [
            {
                "name": "吐司",
                "amount": "2 片",
                "main": True,
            },
            {
                "name": "鸡蛋",
                "amount": "1 个",
                "main": True,
            },
            {
                "name": "生菜",
                "amount": "2 片",
            },
            {
                "name": "番茄片",
                "amount": "2 片",
            },
            {
                "name": "沙拉酱",
                "amount": "1 勺",
            },
        ],
        "steps": [
            {
                "title": "烤吐司",
                "desc": "吐司烤至两面微黄，增加脆感不易软塌。",
                "minutes": 3,
            },
            {
                "title": "煎蛋皮",
                "desc": "鸡蛋打散加少许盐，小火摊成薄蛋皮。",
                "minutes": 2,
            },
            {
                "title": "组装",
                "desc": "依次铺生菜、蛋皮、番茄片，抹沙拉酱后合起对角切开。",
                "minutes": 3,
            },
        ],
        "tips": "生菜洗净后要用厨房纸吸干，水分是面包软化的元凶。",
    },
}

GENERATE_POOL: dict[str, list[str]] = {
    "breakfast": ["oat-congee", "millet-porridge", "soy-milk", "scallion-pancake", "steamed-bun", "red-bean-soup", "egg-custard", "boiled-egg", "tea-egg", "whole-wheat-toast", "pancake-fruit", "veggie-sandwich", "fruit-plate"],
    "lunch": ["rice", "tomato-beef", "kung-pao-chicken", "braised-pork", "sweet-sour-ribs", "pepper-pork", "braised-chicken", "mapo-tofu", "garlic-broccoli", "vinegar-cabbage", "stir-greens", "lotus-root", "oil-bean-sprouts", "steamed-fish"],
    "dinner": ["rice", "shrimp-noodle", "cold-noodle", "beef-noodle", "dumplings", "steamed-fish", "braised-chicken", "tofu-soup", "chicken-soup", "winter-melon-soup", "seaweed-egg-soup", "pumpkin-soup", "spinach-vermicelli", "radish-pickle", "cucumber-salad"],
}

TAG_META: dict[str, dict[str, str]] = {
    "light": {
        "label": "清淡",
        "color": "success",
    },
    "meat": {
        "label": "荤菜",
        "color": "danger",
    },
    "veg": {
        "label": "素菜",
        "color": "success",
    },
    "soup": {
        "label": "汤羹",
        "color": "info",
    },
    "staple": {
        "label": "主食",
        "color": "warn",
    },
    "spicy": {
        "label": "辛辣",
        "color": "danger",
    },
    "quick": {
        "label": "快手",
        "color": "info",
    },
    "warming": {
        "label": "暖胃",
        "color": "warn",
    },
}

WEEK_META: dict[str, str] = {
    "week": "第 1 周",
    "range": "10/20 - 10/26",
}
