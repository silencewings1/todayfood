"""菜品池

从前端 src/data/foods.js 迁移而来，字段保持一致。
每道菜包含：基础信息、标签、星级、推荐理由、签文、烹饪信息。
"""
from __future__ import annotations

from typing import TypedDict


class FoodTags(TypedDict):
    mood: list[str]
    scene: list[str]
    budget: list[str]
    flavor: list[str]


class Food(TypedDict):
    id: str
    title: str
    category: str
    tags: FoodTags
    stars: list[int]
    reason: str
    sign: str
    signName: str
    level: str
    luckyFlavor: str
    luckyColor: str
    direction: str
    cookTime: str
    difficulty: str
    ingredients: list[str]
    steps: list[str]
    tip: str


food_pool: list[Food] = [
    {
        "id": "tomato-beef",
        "title": "番茄牛腩饭",
        "category": "治愈系主食",
        "tags": {"mood": ["hungry", "treat", "tired", "sad"], "scene": ["lunch", "dinner"], "budget": ["normal", "treat"], "flavor": ["sour-sweet", "savory"]},
        "stars": [5, 4, 5],
        "reason": "酸甜的番茄汤底配软烂牛腩，胃被熨平了，今天的小疲惫一起被盖住。",
        "sign": "今日宜热汤主食，先暖胃，再想人生大事。",
        "signName": "热汤主食签",
        "level": "上上签",
        "luckyFlavor": "酸甜",
        "luckyColor": "暖橙",
        "direction": "东南",
        "cookTime": "50 分钟",
        "difficulty": "中等",
        "ingredients": ["牛腩 400g", "番茄 2 个", "洋葱 半个", "米饭 1 碗", "姜片 3 片", "料酒 1 勺"],
        "steps": [
            "牛腩切块冷水下锅，加姜片和料酒焯水 5 分钟，捞出用温水洗净血沫。",
            "番茄顶部划十字，用开水烫 1 分钟后剥皮，切成小块。",
            "热锅少油爆香洋葱丝，加入牛腩块翻炒 2 分钟至表面微黄。",
            "倒入番茄块炒出红汁，加入没过牛腩的热水，大火烧开转小火炖 40 分钟。",
            "加盐和白胡椒调味，米饭盛入碗中，浇上番茄牛腩和汤汁即可。"
        ],
        "tip": "牛腩要炖到筷子能轻松戳进去的程度，最后 5 分钟大火收汁会更香浓。"
    },
    {
        "id": "wonton-noodle",
        "title": "鸡汤云吞面",
        "category": "安稳系汤面",
        "tags": {"mood": ["no-appetite", "hungry", "tired", "sad", "busy"], "scene": ["lunch", "dinner", "late"], "budget": ["normal"], "flavor": ["light", "fresh"]},
        "stars": [5, 4, 5],
        "reason": "清亮的鸡汤底，三只云吞安安静静躺在面上，吃完整个人都跟着被顺毛。",
        "sign": "今日宜清汤面，让肠胃和心情一起轻一点。",
        "signName": "清汤安神签",
        "level": "上签",
        "luckyFlavor": "清淡",
        "luckyColor": "米白",
        "direction": "正南",
        "cookTime": "20 分钟",
        "difficulty": "简单",
        "ingredients": ["鸡汤 500ml", "云吞 6-8 个", "细面 1 把", "小葱 2 根", "姜片 3 片", "生抽 几滴"],
        "steps": [
            "鸡汤加姜片煮开，转小火保持微沸。",
            "另起一锅沸水，下面条煮 2-3 分钟，捞出过冷水沥干。",
            "鸡汤中下云吞，煮到浮起后再煮 1 分钟。",
            "面条放入碗中，浇入滚烫的鸡汤。",
            "摆上云吞，撒上葱花，滴几滴生抽提鲜。"
        ],
        "tip": "没有现成鸡汤，可以用浓汤宝加鸡架骨快速吊 15 分钟，味道也能到 80 分。"
    },
    {
        "id": "spicy-pot",
        "title": "麻辣香锅",
        "category": "提神系硬菜",
        "tags": {"mood": ["spicy", "hungry", "sad", "happy"], "scene": ["dinner", "party"], "budget": ["treat", "normal"], "flavor": ["spicy", "heavy", "sour-spicy"]},
        "stars": [4, 5, 3],
        "reason": "花椒辣椒一激灵，今天的脑子从午后的昏沉里被捞出来，重启成功。",
        "sign": "一点辣意可以唤醒精神，但今天别逞强，记得配一杯凉茶。",
        "signName": "提神醒脑签",
        "level": "中吉",
        "luckyFlavor": "微辣",
        "luckyColor": "正红",
        "direction": "正西",
        "cookTime": "25 分钟",
        "difficulty": "简单",
        "ingredients": ["莲藕 1 节", "土豆 1 个", "木耳 50g", "午餐肉 100g", "鲜虾 100g", "麻辣香锅底料 1 份", "葱姜蒜 适量"],
        "steps": [
            "所有蔬菜切好，土豆和莲藕切薄片泡水 5 分钟去淀粉。",
            "沸水把蔬菜和虾分别焯水 1-2 分钟，捞出沥干水分。",
            "热锅多油，下葱姜蒜爆香，午餐肉煎到两面微焦。",
            "加入底料小火炒出红油，倒入所有食材。",
            "大火快速翻炒 2-3 分钟，让食材均匀裹上红油即可出锅。"
        ],
        "tip": "底料一定要小火慢炒才香，配菜可以换成冰箱里任何你喜欢的食材。"
    },
    {
        "id": "sour-noodle",
        "title": "酸辣粉",
        "category": "提神系小吃",
        "tags": {"mood": ["spicy", "hungry", "sad", "busy"], "scene": ["late", "lunch"], "budget": ["save"], "flavor": ["spicy", "sour-spicy"]},
        "stars": [4, 5, 3],
        "reason": "酸辣开胃，嗦粉声自带解压白噪音，吃完整个人都活过来了。",
        "sign": "今日宜重口味，让味觉替你说出没说出口的话。",
        "signName": "酸辣开胃签",
        "level": "中签",
        "luckyFlavor": "酸辣",
        "luckyColor": "亮黄",
        "direction": "正东",
        "cookTime": "20 分钟",
        "difficulty": "简单",
        "ingredients": ["红薯粉 1 把", "花生碎 1 把", "香菜 2 根", "蒜末 1 勺", "生抽 2 勺", "陈醋 3 勺", "辣椒油 1 勺", "白芝麻 少许"],
        "steps": [
            "红薯粉用温水泡 15 分钟至变软。",
            "调料汁：蒜末 + 生抽 + 陈醋 + 辣椒油 + 少量糖，搅拌均匀。",
            "烧水，水开后下粉条煮 3 分钟（没泡的话煮 5 分钟）。",
            "捞出粉条过冷水沥干，倒入调料汁拌匀。",
            "撒上花生碎、白芝麻和香菜末即可。"
        ],
        "tip": "醋分两次加味道更立体——一次调味，一次出锅前激香气。"
    },
    {
        "id": "springroll",
        "title": "越南春卷轻食碗",
        "category": "清爽系轻食",
        "tags": {"mood": ["no-appetite", "treat", "happy", "tired"], "scene": ["lunch", "dinner"], "budget": ["normal", "treat"], "flavor": ["light", "fresh"]},
        "stars": [4, 3, 5],
        "reason": "薄荷、青芒果、米线、香茅，少油少负担，吃完身体会悄悄感谢你。",
        "sign": "今日宜清爽，让身体和心情都轻一点。",
        "signName": "清风轻食签",
        "level": "上签",
        "luckyFlavor": "清淡",
        "luckyColor": "薄荷绿",
        "direction": "正北",
        "cookTime": "30 分钟",
        "difficulty": "中等",
        "ingredients": ["米纸 4 张", "鲜虾 8 只", "鸡胸肉 100g", "生菜 适量", "薄荷 1 小把", "青芒果 半个", "米线 50g"],
        "steps": [
            "米线煮熟过冷水，虾去壳去虾线煮熟，鸡胸肉煮熟撕成丝。",
            "米纸放入温水中泡 10 秒变软，取出铺在湿布上。",
            "米纸底部铺生菜叶，依次放米线、虾、鸡丝、薄荷。",
            "两侧向内折起，从下往上卷紧。",
            "配上鱼露酸甜汁或花生酱一起吃。"
        ],
        "tip": "米纸不要泡太久会破，包的时候底下垫湿布防粘。"
    },
    {
        "id": "cold-chicken",
        "title": "凉拌鸡丝荞麦面",
        "category": "清爽系凉面",
        "tags": {"mood": ["no-appetite", "spicy", "tired", "happy"], "scene": ["lunch", "late"], "budget": ["normal"], "flavor": ["spicy", "light", "sour-spicy", "fresh"]},
        "stars": [4, 4, 4],
        "reason": "冰镇过的荞麦面裹着辣油和芝麻酱，凉下来就是夏天最对的一口。",
        "sign": "今日宜冷食，让体温先休息一下。",
        "signName": "夏日凉食签",
        "level": "中吉",
        "luckyFlavor": "微辣",
        "luckyColor": "薄荷绿",
        "direction": "东北",
        "cookTime": "25 分钟",
        "difficulty": "简单",
        "ingredients": ["荞麦面 1 把", "鸡胸肉 1 块", "黄瓜 半根", "胡萝卜 半根", "芝麻酱 2 勺", "醋 1 勺", "蒜末 1 勺"],
        "steps": [
            "鸡胸肉冷水下锅加姜片煮 15 分钟，捞出过冰水后撕成丝。",
            "荞麦面沸水煮 3-4 分钟，捞出过冷水沥干。",
            "黄瓜和胡萝卜切成细丝。",
            "芝麻酱加醋、生抽、少量糖、蒜末调匀（太稠加一点温水）。",
            "面条装盘，铺上鸡丝和蔬菜丝，淋上酱汁拌匀即可。"
        ],
        "tip": "面条过冰水会更 Q 弹，芝麻酱太稠一定要加温水才能拌开。"
    },
    {
        "id": "korean-army",
        "title": "韩式部队锅",
        "category": "社交系大餐",
        "tags": {"mood": ["treat", "hungry", "happy", "sad"], "scene": ["party", "dinner"], "budget": ["treat"], "flavor": ["spicy", "heavy", "milky"]},
        "stars": [5, 5, 4],
        "reason": "年糕、拉面、芝士、午餐肉，所有快乐信号在一锅里开大会。",
        "sign": "今日宜分享，一个人吃是饱，一群人吃是热闹。",
        "signName": "热闹聚餐签",
        "level": "上上签",
        "luckyFlavor": "辛甜",
        "luckyColor": "番茄红",
        "direction": "东南",
        "cookTime": "15 分钟",
        "difficulty": "简单",
        "ingredients": ["辛拉面 1 包", "午餐肉 100g", "年糕 100g", "芝士年糕 1 块", "泡菜 100g", "金针菇 1 把", "小香肠 4 根"],
        "steps": [
            "铸铁锅或深一点的小奶锅底层铺上泡菜。",
            "依次摆上年糕、午餐肉片、金针菇、小香肠。",
            "加入刚好没过食材的清水，大火煮开。",
            "下辛拉面和调料包，搅匀后摆正。",
            "面上铺一片芝士年糕，盖盖子焖到芝士完全融化。"
        ],
        "tip": "没有铸铁锅用深一点的炒锅也行，芝士是灵魂千万别省。"
    },
    {
        "id": "yellow-chicken",
        "title": "黄焖鸡米饭",
        "category": "稳定系快餐",
        "tags": {"mood": ["hungry", "no-appetite", "busy", "tired"], "scene": ["lunch", "dinner"], "budget": ["save", "normal"], "flavor": ["heavy", "savory"]},
        "stars": [4, 4, 4],
        "reason": "酱香浓郁、米饭粒粒入味，是不会出错的稳妥选择，胃永远给好评。",
        "sign": "今日宜稳妥，把\"不知道吃什么\"的焦虑交给熟悉的味道。",
        "signName": "稳健米饭签",
        "level": "上签",
        "luckyFlavor": "酱香",
        "luckyColor": "姜黄",
        "direction": "正南",
        "cookTime": "30 分钟",
        "difficulty": "简单",
        "ingredients": ["鸡腿肉 300g", "香菇 6 朵", "青椒 1 个", "干辣椒 3 个", "黄焖鸡酱料 1 份", "姜片 3 片"],
        "steps": [
            "鸡腿肉切块冷水下锅焯水 3 分钟，捞出洗净血沫。",
            "香菇泡发切片，青椒切滚刀块。",
            "热锅少油，下干辣椒和姜片爆香。",
            "加鸡块翻炒 1 分钟，加香菇和酱料拌匀。",
            "加水没过食材，中火焖 15 分钟。",
            "加入青椒再焖 2 分钟，浇在米饭上即可。"
        ],
        "tip": "鸡腿肉比鸡胸肉更嫩多汁，没有酱料可用生抽+老抽+糖+蚝油 1:1:1:1 替代。"
    },
    {
        "id": "lanzhou-noodle",
        "title": "兰州牛肉面",
        "category": "稳定系汤面",
        "tags": {"mood": ["hungry", "treat", "tired", "sad"], "scene": ["lunch", "dinner"], "budget": ["normal", "save"], "flavor": ["light", "heavy", "savory", "fresh"]},
        "stars": [5, 4, 5],
        "reason": "一清二白三红四绿五黄，汤清味正，吃完连呼吸都是稳的。",
        "sign": "今日宜清汤牛肉面，朴素里藏着最深的治愈。",
        "signName": "清汤牛肉签",
        "level": "上上签",
        "luckyFlavor": "清淡",
        "luckyColor": "麦黄",
        "direction": "西北",
        "cookTime": "2 小时",
        "difficulty": "进阶",
        "ingredients": ["牛肉 300g", "牛骨 1 根", "面条 1 把", "白萝卜 半根", "姜片 5 片", "花椒 10 粒", "香菜蒜苗 少许"],
        "steps": [
            "牛肉和牛骨冷水下锅焯水 5 分钟，捞出洗净。",
            "重新加水加姜片和花椒，大火煮开后转小火炖 1.5 小时。",
            "白萝卜切块，最后 30 分钟加入。",
            "另一锅沸水煮面 2-3 分钟捞出。",
            "面条盛入碗中，摆上切好的牛肉片和萝卜块。",
            "浇入清亮牛肉汤，撒上香菜和蒜苗即可。"
        ],
        "tip": "汤要清亮关键是大火煮开时撇去浮沫，然后小火慢炖不加盖。"
    },
    {
        "id": "cheese-pizza",
        "title": "芝士披萨",
        "category": "快乐系放纵",
        "tags": {"mood": ["treat", "hungry", "happy", "sad"], "scene": ["party", "dinner", "late"], "budget": ["treat"], "flavor": ["heavy", "milky"]},
        "stars": [4, 5, 4],
        "reason": "芝士拉丝的瞬间，今天所有不开心都被拉成可以忽略的远景。",
        "sign": "今日宜奖励自己，热量先欠着，心情先收下。",
        "signName": "快乐放纵签",
        "level": "中吉",
        "luckyFlavor": "奶香",
        "luckyColor": "芝士黄",
        "direction": "正西",
        "cookTime": "20 分钟",
        "difficulty": "简单",
        "ingredients": ["9 寸披萨饼底 1 个", "马苏里拉芝士 200g", "番茄酱 4 勺", "蘑菇 4 朵", "青椒 1 个", "培根 2 片"],
        "steps": [
            "烤箱预热 220°C。",
            "饼底均匀涂一层番茄酱。",
            "撒一层芝士，放蘑菇片、青椒圈、培根碎。",
            "再撒一层芝士把配料盖住。",
            "放入烤箱中层烤 12-15 分钟，到芝士金黄起泡即可。"
        ],
        "tip": "没有烤箱可以用平底锅小火盖盖子焖 10 分钟，出锅前淋一圈橄榄油更香。"
    },
    {
        "id": "claypot-rice",
        "title": "广式煲仔饭",
        "category": "治愈系主食",
        "tags": {"mood": ["hungry", "treat", "tired", "happy"], "scene": ["lunch", "dinner"], "budget": ["normal", "treat"], "flavor": ["heavy", "savory"]},
        "stars": [5, 4, 5],
        "reason": "锅巴的焦香是整碗饭的灵魂，最后一勺饭总是最对的一口。",
        "sign": "今日宜慢火煲一锅饭，时间花在哪，味道就在哪。",
        "signName": "慢火煲仔签",
        "level": "上签",
        "luckyFlavor": "酱香",
        "luckyColor": "焦糖",
        "direction": "正南",
        "cookTime": "50 分钟",
        "difficulty": "中等",
        "ingredients": ["大米 1 杯", "腊肠 2 根", "腊肉 50g", "油菜 2 棵", "鸡蛋 1 个", "酱油 1 勺", "香油 几滴"],
        "steps": [
            "大米淘洗后浸泡 30 分钟。",
            "砂锅刷一层香油，放入米和水（1:1.2 比例）。",
            "大火煮开后转小火焖 8 分钟。",
            "摆上切片的腊肠和腊肉，盖盖再焖 5 分钟。",
            "中间打入一个鸡蛋，盖盖焖 2 分钟。",
            "油菜焯水摆在饭上，淋上酱油拌匀。"
        ],
        "tip": "最后 30 秒开大火让底部形成锅巴，是煲仔饭的灵魂，记得听焦香味。"
    },
    {
        "id": "congee",
        "title": "皮蛋瘦肉砂锅粥",
        "category": "治愈系汤粥",
        "tags": {"mood": ["no-appetite", "tired", "sad", "busy"], "scene": ["dinner", "late"], "budget": ["save", "normal"], "flavor": ["light", "fresh", "savory"]},
        "stars": [5, 5, 5],
        "reason": "米粒煮到绵密、皮蛋切到细碎，胃被裹进一碗温热的柔软里。",
        "sign": "今日宜粥米，胃难受的时候，最朴素的选择最治愈。",
        "signName": "温润砂粥签",
        "level": "上上签",
        "luckyFlavor": "清淡",
        "luckyColor": "米白",
        "direction": "正北",
        "cookTime": "45 分钟",
        "difficulty": "中等",
        "ingredients": ["大米 1/2 杯", "瘦肉 100g", "皮蛋 2 个", "姜丝 1 勺", "葱花 1 勺", "淀粉 少许"],
        "steps": [
            "大米淘洗后加水（1:8）大火煮开。",
            "转小火慢熬 30 分钟，期间不时搅拌防粘底。",
            "瘦肉切丝，用生抽和淀粉腌 10 分钟。",
            "皮蛋剥壳切成小丁。",
            "粥熬好后下肉丝、皮蛋丁、姜丝，再煮 5 分钟。",
            "出锅前撒葱花，加盐和白胡椒调味即可。"
        ],
        "tip": "想要更绵绸可以加几滴油一起熬，粥底要一直保持微沸状态。"
    }
]


def find_food(food_id: str) -> Food | None:
    """根据 id 查找菜品"""
    for f in food_pool:
        if f["id"] == food_id:
            return f
    return None
