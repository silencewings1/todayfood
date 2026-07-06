/**
 * 传统黄历宜忌数据池
 * 用于"今日食历"卡的传统黄历部分，与干饭宜忌并列展示
 */

// 黄历"宜"项池（每日随机挑 3-4 条）
export const almanacYiPool = [
  '祭祀', '祈福', '开光', '出行', '解除', '入宅', '移徙',
  '安床', '修造', '动土', '上梁', '开市', '交易', '立券',
  '挂匾', '纳财', '栽种', '纳畜', '启钻', '拆卸', '伐木',
  '经络', '酝酿', '理发', '整手足甲', '冠笄', '会亲友',
  '进人口', '裁衣', '结网', '作灶', '破屋', '坏垣', '余事勿取'
]

// 黄历"忌"项池（每日随机挑 2-3 条）
export const almanacJiPool = [
  '嫁娶', '安葬', '行丧', '破土', '开市', '动土', '出行',
  '祈福', '入宅', '移徙', '安床', '修造', '上梁', '交易',
  '立券', '纳财', '栽种', '纳畜', '针灸', '伐木', '经络',
  '理发', '会亲友', '作灶', '冠笄', '裁衣', '结网', '词讼',
  '出火', '归宁'
]

/** 按种子挑黄历宜项（3-4 条） */
export function pickAlmanacYi(seed) {
  const rand = (() => {
    let s = seed + 53
    return () => {
      s = (s * 9301 + 49297) % 233280
      return s / 233280
    }
  })()
  const count = 3 + Math.floor(rand() * 2)
  const shuffled = [...almanacYiPool].sort(() => rand() - 0.5)
  return shuffled.slice(0, count)
}

/** 按种子挑黄历忌项（2-3 条） */
export function pickAlmanacJi(seed) {
  const rand = (() => {
    let s = seed + 89
    return () => {
      s = (s * 9301 + 49297) % 233280
      return s / 233280
    }
  })()
  const count = 2 + Math.floor(rand() * 2)
  const shuffled = [...almanacJiPool].sort(() => rand() - 0.5)
  return shuffled.slice(0, count)
}
