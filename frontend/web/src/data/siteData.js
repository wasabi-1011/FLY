// ============================================================
// FLY 前台 · 共享静态数据层（占位）
// 字段刻意对齐后端公开接口（GET /api/products/*、/api/news/*、/api/stores/*），
// 后续接 API 时只需替换本文件的取数函数，页面组件不变。
// 约束：不出现价格/库存/销量（PRD N5）；hot 为运营人工标记（N12）。
// ============================================================

// ---- 品类元信息 -------------------------------------------------
export const CATEGORIES = [
  {
    key: "women",
    label: "女装",
    en: "WOMEN",
    hero: "/pic/series-women.jpg",
    slogan: "都市游牧的硬朗与轻盈",
    intro: "为穿梭于城市与旷野之间的她而作：利落廓形、机能面料与柔和细节并存，一件衣服足以完成从通勤到出行的切换。",
  },
  {
    key: "men",
    label: "男装",
    en: "MEN",
    hero: "/pic/series-men.jpg",
    slogan: "从格子间到山野的切换",
    intro: "为不被定义场景的男士而作：结构剪裁结合功能面料，克制而耐穿，让城市通勤与户外探索共用同一件装备。",
  },
  {
    key: "kids",
    label: "童装",
    en: "KIDS",
    hero: "/pic/series-kids.jpg",
    slogan: "陪伴每一次天真探索",
    intro: "为好奇的小小探险家而作：亲肤面料、耐磨结构与免束缚的版型，让孩子在奔跑、攀爬与成长中始终自在。",
  },
];

// ---- 系列（每系列内含款式 items） --------------------------------
export const SERIES = [
  {
    cat: "women",
    name: "城野机能",
    en: "CITY WILD",
    season: "2026 秋冬",
    cover: "/pic/series-women.jpg",
    desc: "以城市为起点、山野为终点的一组日常机能单品：防泼水、四面弹与人体工学剪裁，藏进克制的都市轮廓里。",
    items: [
      { code: "CO-SW001", name: "廓形短风衣", hot: true, img: "/pic/hot-01.jpg", desc: "防泼水面料 + 利落廓形，通勤与城野两相宜。" },
      {
        code: "CO-SW003", name: "高领针织", hot: true, img: "/pic/hot-03.jpg",
        desc: "柔软羊毛混纺，高领贴合，冷天里的温柔护盾。",
        story: "一件好的高领针织，是冬天的第二层皮肤。羊毛混纺带来恰到好处的暖意与弹性，高领结构贴合颈部线条，单穿或作内搭都成立。",
        points: ["羊毛混纺纱线，软糯亲肤不过敏", "高领贴合不勒，冷风灌不进来", "微弹罗纹收边，久穿不易变形", "米金/墨黑低饱和色系，易搭外套"],
        fabric: "羊毛 + 再生纤维混纺纱线（示例文案）",
        care: "建议干洗或手洗平铺晾干，避免悬挂变形（示例文案）",
      },
      { code: "CO-SW007", name: "泡泡袖衬衫", hot: true, img: "/pic/hot-07.jpg", desc: "复古泡泡袖的轻盈轮廓，通勤与周末皆可穿。" },
    ],
  },
  {
    cat: "men",
    name: "无界通勤",
    en: "BOUNDLESS COMMUTE",
    season: "2026 秋冬",
    cover: "/pic/series-men.jpg",
    desc: "打破通勤与户外的边界：耐磨外壳、可收纳结构与克制的配色，让一套行头覆盖一天的所有场景。",
    items: [
      { code: "CO-MN002", name: "机能羽绒马甲", hot: true, img: "/pic/hot-02.jpg", desc: "轻暖羽绒 + 机能外袋，叠穿点睛也足够保暖。" },
      { code: "CO-MN004", name: "工装背带裤", hot: true, img: "/pic/hot-04.jpg", desc: "多袋工装结构，耐磨棉感，自在又有型。" },
      { code: "CO-MN006", name: "机能冲锋衣", hot: true, img: "/pic/hot-06.jpg", desc: "防风防水三合一，一件应对城市风雨与山野气候。" },
    ],
  },
  {
    cat: "kids",
    name: "小小探险家",
    en: "LITTLE EXPLORER",
    season: "2026 秋冬",
    cover: "/pic/series-kids.jpg",
    desc: "为 4–12 岁的小小探险家设计：A 类亲肤面料、耐磨结构与免束缚版型，守护每一次好奇的奔跑。",
    items: [
      { code: "CO-KD005", name: "亲子卫衣", hot: true, img: "/pic/hot-05.jpg", desc: "软糯亲肤棉，亲子同款，把陪伴穿在身上。" },
      {
        code: "CO-KD008", name: "灯芯绒外套", hot: true, img: "/pic/hot-08.jpg",
        desc: "复古灯芯绒，耐磨易洗，秋冬探索的暖心外衣。",
        story: "给小小探险家的秋冬外衣，选择了耐磨又温暖的灯芯绒。复古肌理耐看耐穿，宽松剪裁留足奔跑空间，脏了直接丢洗衣机，妈妈省心。",
        points: ["A 类亲肤面料，安心接触皮肤", "复古灯芯绒肌理，耐磨易打理", "宽松剪裁，内搭卫衣也活动自如", "撞色贴袋 + 按扣设计，孩子易穿"],
        fabric: "A 类标准棉质灯芯绒（示例文案）",
        care: "可机洗，反面洗涤可减少起毛（示例文案）",
      },
    ],
  },
];

// ---- 查询 helper（对齐后端返回结构的使用方式） --------------------
export const getCategory = (key) => CATEGORIES.find((c) => c.key === key);
export const getSeriesByCat = (cat) => SERIES.filter((s) => s.cat === cat);
export const getItemsByCat = (cat) =>
  SERIES.flatMap((s) => (s.cat === cat ? s.items.map((i) => ({ ...i, cat: s.cat, series: s.name })) : []));
export const getAllItems = () =>
  SERIES.flatMap((s) => s.items.map((i) => ({ ...i, cat: s.cat, series: s.name })));
// 单品详情：按 品类 + 款号 查找，返回 { category, series, item }
export const findItem = (catKey, code) => {
  const s = SERIES.find((x) => x.cat === catKey && x.items.some((i) => i.code === code));
  if (!s) return null;
  const c = getCategory(catKey);
  return { category: c, series: s, item: s.items.find((i) => i.code === code) };
};
// 相关推荐：同品类除当前款外的其它款式（同系列优先排列，按款号去重）
export const getRelatedItems = (catKey, code) => {
  const sameSeries = SERIES.find((x) => x.cat === catKey && x.items.some((i) => i.code === code));
  const codes = [code, ...(sameSeries ? sameSeries.items.map((i) => i.code) : [])];
  const all = getItemsByCat(catKey).filter((i) => !codes.includes(i.code));
  const sameSeriesOthers = (sameSeries ? sameSeries.items.filter((i) => i.code !== code) : []);
  return [...sameSeriesOthers, ...all].slice(0, 3);
};
export const itemDetailPath = (cat, code) => `/products/${cat}/${code}`;

// 首页「热门推荐」顺序（沿用 hot-01..08 图序，运营人工打标）
export const HOT_ORDER = [
  "CO-SW001", "CO-MN002", "CO-SW003", "CO-MN004", "CO-KD005", "CO-MN006", "CO-SW007", "CO-KD008",
];
export const getHotItems = () => {
  const all = getAllItems();
  return HOT_ORDER.map((code) => all.find((i) => i.code === code)).filter(Boolean);
};

// 首页三大系列封面卡片（当季系列推荐）
export const HOME_COLLECTIONS = CATEGORIES.map((c) => {
  const s = getSeriesByCat(c.key)[0];
  return {
    cat: c.key,
    tag: `${c.label} ${c.en}`,
    title: s.name,
    desc: s.desc,
    img: c.hero,
  };
});

// ---- 新闻（company 企业新闻 / industry 行业资讯） -------------------
// body 节点类型：lead 引语 | p 段落 | h 小节标题 | quote 引用 | img 插图(src/cap)
export const NEWS = [
  // ===== 企业新闻 =====
  {
    cat: "company",
    slug: "aw-2026-global-launch",
    title: "FLY 2026 秋冬系列全球发布：让城市与山野同频",
    date: "2026-09-07",
    place: "上海",
    editor: "FLY 品牌部",
    cover: "/pic/news-01.jpg",
    lead: "9 月 7 日晚，FLY 在上海西岸以「城野机能 CITY WILD」为主题发布 2026 秋冬全系列，女装、男装与童装三条线同台亮相。",
    body: [
      { t: "p", v: "发布会以一座室内「山野」装置开场——苔原、碎石与城市天际线投影交织，呼应本季「从格子间到山野」的叙事主线。模特穿梭其间，完成了都市通勤与户外探索两种场景的无缝切换。" },
      { t: "h", v: "三个系列，一个命题：穿出自我" },
      { t: "p", v: "女装「城野机能」以利落廓形与防泼水面料回应都市游牧的日常；男装「无界通勤」强调结构剪裁与三合一机能；童装「小小探险家」则专注 A 类亲肤面料与免束缚版型。三个系列共享同一句主张——穿出自我，随心而飞。" },
      { t: "img", src: "/pic/series-women.jpg", cap: "FLY 2026 秋冬 · 女装「城野机能」系列大片" },
      { t: "quote", v: "我们不定义风格，只提供让每个人找到自己的可能。" },
      { t: "p", v: "即日起，新系列陆续登陆全国 8 城 20 家门店与线上官方渠道。FLY 会员可于门店优先试穿并参与系列主题活动。" },
    ],
  },
  {
    cat: "company",
    slug: "shenzhen-qixiang-flagship",
    title: "FLY 深圳万象天地旗舰店开幕：让「看到」变为「找到」",
    date: "2026-09-01",
    place: "深圳",
    editor: "FLY 品牌部",
    cover: "/pic/news-02.jpg",
    lead: "9 月 1 日，FLY 华南首家旗舰店于深圳万象天地正式启幕，双层空间首次完整呈现全品类陈列与品牌体验区。",
    body: [
      { t: "p", v: "新店选址深圳万象天地高街，临街双层玻璃立面将产品与街景相连。一层为女装与童装主场，二层为男装与「FLY 档案」品牌展示区，陈列历年代表面料与设计手稿。" },
      { t: "img", src: "/pic/banner-03.jpg", cap: "深圳万象天地旗舰店开幕活动现场" },
      { t: "p", v: "开幕首周，门店同步上线城市限定配色系列，并开放「旧衣焕新」计划：携任意 FLY 旧衣到店即可参与面料回收，换取当季配件礼遇。" },
      { t: "p", v: "截至目前，FLY 已覆盖北京、上海、广州、深圳、成都、杭州、武汉、南京 8 城共 20 家门店，全国门店地图与城市查询已同步更新。" },
    ],
  },
  {
    cat: "company",
    slug: "hangzhou-in77-renovation",
    title: "杭州湖滨银泰 in77 店焕新启幕",
    date: "2026-08-18",
    place: "杭州",
    editor: "FLY 品牌部",
    cover: "/pic/banner-02.jpg",
    lead: "经过两个月改造，FLY 杭州湖滨银泰 in77 店以全新空间形象回归，成为品牌在华东的又一重要坐标。",
    body: [
      { t: "p", v: "焕新后的门店采用「暖木 × 金属」的材质对话：橡木展架带来温度，拉丝金属呼应机能面料的语言。试衣区被设计成半开放「小屋」，让顾客在松弛中完成试穿。" },
      { t: "h", v: "更多城市互动" },
      { t: "p", v: "门店二层增设「杭州城市限定角」，首发西湖意象的丝巾与配件系列，仅在杭州门店与线上会员店限量供应。" },
      { t: "p", v: "老店焕新首月，门店同步开启会员到店礼遇。具体营业时间与到店指引，可通过官网「门店查询」页查看。" },
    ],
  },
  {
    cat: "company",
    slug: "sustainability-report-2026",
    title: "FLY 发布 2026 可持续时尚报告：让每件衣服走得更远",
    date: "2026-08-08",
    place: "上海",
    editor: "可持续发展小组",
    cover: "/pic/brand.jpg",
    lead: "FLY 正式发布《2026 可持续时尚报告》，首次披露面料采购、生产能耗与门店旧衣回收三组年度数据。",
    body: [
      { t: "p", v: "报告显示，2026 秋冬系列中约 42% 的主面料采用再生或可追溯纤维，较上一财年提升 9 个百分点；两座合作工厂的单位产量用水同比下降 12%。" },
      { t: "quote", v: "可持续不是营销词，是每一件衣服从设计到回收的完整旅程。" },
      { t: "h", v: "旧衣焕新计划升级" },
      { t: "p", v: "本季起，「旧衣焕新」回收计划从旗舰店推广至全部 20 家门店：任意品牌旧衣均可到店回收，兑换配件礼遇；回收面料将进入再生供应链，制成次年配件系列。" },
    ],
  },
  {
    cat: "company",
    slug: "capsule-collab-preview",
    title: "FLY × 独立设计师联名胶囊系列预告",
    date: "2026-07-30",
    place: "线上发布",
    editor: "FLY 品牌部",
    cover: "/pic/series-women.jpg",
    lead: "FLY 宣布与三位新锐独立设计师展开联名，胶囊系列将于秋冬中段上线，主打「可拆解、可重组」的模块化穿着。",
    body: [
      { t: "p", v: "该系列邀请来自上海、成都与伦敦的三位设计师，围绕「一衣多穿」展开创作：可拆卸帽领、可互换扣件与可卷收纳结构，成为系列三大关键词。" },
      { t: "img", src: "/pic/news-01.jpg", cap: "联名胶囊系列设计手稿（示意）" },
      { t: "p", v: "胶囊系列预计于 11 月登陆线上官方渠道与北京、上海两家旗舰店。更多细节将在「企业新闻」栏目持续更新。" },
    ],
  },
  // ===== 行业资讯 =====
  {
    cat: "industry",
    slug: "aw-2026-fabric-trends",
    title: "2026 秋冬面料趋势观察：功能回归日常",
    date: "2026-08-26",
    place: "编辑部",
    editor: "趋势小组",
    cover: "/pic/news-03.jpg",
    lead: "从本季各大品牌发布来看，防泼水、四面弹与再生纤维不再是「户外专属」，正大规模进入都市日常装束。",
    body: [
      { t: "p", v: "过去五年，「机能」从冲锋衣上的技术标签，演变为衬衫、针织甚至童装中的日常语言。2026 秋冬，这一趋势进一步分化出两个方向：一是「看不见的机能」——面料功能被藏在柔软手感之后；二是「结构机能」——以可拆卸、可收纳的设计承载功能。" },
      { t: "h", v: "再生纤维的占比之变" },
      { t: "p", v: "越来越多品牌公布再生纤维使用比例，并以此作为供应链透明度的一部分。对消费者而言，「这件衣服用什么做的」正在成为与版型、颜色同等重要的购买决策因素。" },
      { t: "img", src: "/pic/series-men.jpg", cap: "功能面料在城市通勤场景中的应用（示意）" },
    ],
  },
  {
    cat: "industry",
    slug: "store-digital-observation",
    title: "门店数字化观察：地图、库存与到店体验如何被重构",
    date: "2026-08-12",
    place: "编辑部",
    editor: "行业观察组",
    cover: "/pic/banner-03.jpg",
    lead: "当消费者习惯「先搜门店、再看地图、再决定到店」，线下零售的入口正在从街角变成手机屏幕上的一个坐标。",
    body: [
      { t: "p", v: "越来越多的服饰品牌把「门店查询」做成官网与小程序的一级入口：城市分组、地图点位、营业状态实时可见。线上「看得见」，正在成为线下「到得了」的前提。" },
      { t: "quote", v: "地图上的一个点，背后是一次真实的到店决策。" },
      { t: "p", v: "与此同时，「有货提示」类功能开始出现：顾客在浏览某件商品时，可查询附近哪些门店有货，把线上浏览与线下试穿连接起来。这类体验依赖门店库存数据的实时性，也是品牌数字化投入的重点方向。" },
    ],
  },
  {
    cat: "industry",
    slug: "urban-outdoor-rise",
    title: "都市户外风潮观察：从功能单品到生活方式",
    date: "2026-07-22",
    place: "编辑部",
    editor: "趋势小组",
    cover: "/pic/series-men.jpg",
    lead: "露营、徒步与城市骑行共同催热的「都市户外」风格，正在从一套穿搭演变为一种可被品牌完整讲述的生活方式。",
    body: [
      { t: "p", v: "都市户外（Urban Outdoor）的核心并非「穿得像要去登山」，而是让功能为日常服务：一件能应对突然降雨的外套、一条耐磨却体面的长裤、一双走一天也不累的鞋。" },
      { t: "h", v: "品牌如何回应" },
      { t: "p", v: "我们看到两类回应：一类以「系列」承载，把户外功能编入当季完整 look；另一类以「门店体验」承载，在店内设置可触摸的面料墙与场景化陈列，让顾客直观理解功能。" },
      { t: "p", v: "可以预见，当功能成为默认项，「风格表达」与「场景适配」将重新成为下一阶段的设计竞争点。" },
    ],
  },
  {
    cat: "industry",
    slug: "kids-fabric-safety",
    title: "童装面料与安全：A 类标准的那些事",
    date: "2026-07-05",
    place: "编辑部",
    editor: "品质小组",
    cover: "/pic/series-kids.jpg",
    lead: "给孩子的衣服，安全标准往往比款式更值得关注。这篇短文梳理童装面料的 A/B/C 分类与选购要点。",
    body: [
      { t: "p", v: "根据 GB 31701，婴幼儿及儿童纺织品按安全技术类别分为 A、B、C 三类：A 类要求最严（甲醛、pH 值、色牢度等限量最紧），适用于 36 个月以下婴幼儿；B 类为直接接触皮肤产品；C 类为非直接接触皮肤产品。" },
      { t: "img", src: "/pic/series-kids.jpg", cap: "童装亲肤面料细节（示意）" },
      { t: "h", v: "选购三看" },
      { t: "p", v: "一看吊牌标注的类别（贴身穿建议选 A 类）；二看面料成分，棉、莫代尔等天然/再生纤维素纤维透气性更佳；三看辅料，拉链头、纽扣是否牢固圆润，避免小零件脱落风险。" },
    ],
  },
];

export const getNewsByCat = (cat) => NEWS.filter((n) => n.cat === cat);
export const getNewsDetail = (cat, slug) => NEWS.find((n) => n.cat === cat && n.slug === slug);
export const formatDate = (d) => d.replace(/-/g, ".");

// ---- 门店城市（GCJ-02；与首页 StoreEntry 一致） --------------------
export const STORE_CITIES = [
  { id: "bj", name: "北京", lng: 116.397428, lat: 39.90923, stores: [
    { n: "三里屯旗舰店", a: "朝阳区三里屯太古里南区 S8-30" }, { n: "国贸店", a: "朝阳区建国门外大街 1 号国贸商城" },
    { n: "西单大悦城店", a: "西城区西单北大街 131 号" }, { n: "王府井店", a: "东城区王府井大街 138 号" } ] },
  { id: "sh", name: "上海", lng: 121.489, lat: 31.227, stores: [
    { n: "南京西路旗舰店", a: "静安区南京西路 1601 号" }, { n: "环贸 iapm 店", a: "徐汇区淮海中路 999 号" },
    { n: "正大广场店", a: "浦东新区陆家嘴西路 168 号" }, { n: "静安大悦城店", a: "静安区西藏北路 198 号" } ] },
  { id: "gz", name: "广州", lng: 113.272, lat: 23.136, stores: [
    { n: "天河城店", a: "天河区天河路 208 号" }, { n: "太古汇店", a: "天河区天河路 383 号" }, { n: "北京路店", a: "越秀区北京路 374 号" } ] },
  { id: "sz", name: "深圳", lng: 114.085, lat: 22.547, stores: [
    { n: "万象天地旗舰店", a: "南山区深南大道 9668 号" }, { n: "万象城店", a: "罗湖区宝安南路 1881 号" }, { n: "海岸城店", a: "南山区文心五路 33 号" } ] },
  { id: "cd", name: "成都", lng: 104.065, lat: 30.659, stores: [
    { n: "IFS 国际金融中心店", a: "锦江区红星路三段 1 号" }, { n: "万象城店", a: "成华区双庆路 8 号" } ] },
  { id: "hz", name: "杭州", lng: 120.153, lat: 30.287, stores: [
    { n: "湖滨银泰 in77 店", a: "上城区延安路 538 号" }, { n: "万象城店", a: "江干区富春路 701 号" } ] },
  { id: "wh", name: "武汉", lng: 114.305, lat: 30.593, stores: [
    { n: "武商广场店", a: "江汉区解放大道 688 号" } ] },
  { id: "nj", name: "南京", lng: 118.797, lat: 32.060, stores: [
    { n: "德基广场店", a: "玄武区中山路 18 号" } ] },
];
export const STORE_TOTAL = STORE_CITIES.reduce((s, c) => s + c.stores.length, 0);
