import os
import io
import json
import math
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PROJECT_ROOT = r"c:\Users\mattu\Documents\MyProjects\pokemon-games"
CARDS_DIR = os.path.join(PROJECT_ROOT, "assets", "cards")
SPRITES_DIR = os.path.join(PROJECT_ROOT, "assets", "sprites")
CRIES_DIR = os.path.join(PROJECT_ROOT, "assets", "audio", "cries")
DATA_DIR = os.path.join(PROJECT_ROOT, "assets", "data")
RAW_CACHE = os.path.join(PROJECT_ROOT, "scripts", "_raw_cache")

for d in [CARDS_DIR, SPRITES_DIR, CRIES_DIR, DATA_DIR, RAW_CACHE]:
    os.makedirs(d, exist_ok=True)

# ==============================================================================
# 75 MAIN BINGO / CARD POKEMON (1-75)
# Tuple: (bingo_id, dex_id, name, rarity, type_key, type_label, emoji, move, quote, spoken_quote)
# Note: All names/labels/moves in katakana/hiragana friendly for kids too!
# ==============================================================================
MAIN_75 = [
    # B列 (1-15): カントー＆超人気スターズ
    (1, 25, "ピカチュウ", "UR", "electric", "でんき", "⚡", "10まんボルト",
     "ほっぺの でんきぶくろから 10まんボルトの でんげきを はなつ さいこうの あいぼう！",
     "じゅうまんボルト！ ほっぺの でんきぶくろから きょうりょくな でんげきを はなつロト！"),
    (2, 6, "リザードン", "UR", "fire", "ほのお・ひこう", "🔥", "ブラストバーン",
     "なんでも とかす しゃくねつの ほのおを はきだし おおぞらを とびまわる！",
     "ブラストバーン！ しゃくねつの ほのおを はきだし おおぞらを かけるロト！"),
    (3, 133, "イーブイ", "SSR", "normal", "ノーマル", "🎀", "とっておき",
     "いろんな すがたに しんかできる ふしぎな かのうせいを ひめた ポケモン！",
     "とっておき！ いろんな すがたに しんかできる ふしぎな パワーを もっているロト！"),
    (4, 150, "ミュウツー", "UR", "psychic", "エスパー", "🔮", "サイコブレイク",
     "さいきょうの サイコパワーを あやつる でんせつの ポケモン！",
     "サイコブレイク！ さいきょうクラスの サイコパワーで すべてを あっとうするロト！"),
    (5, 151, "ミュウ", "UR", "psychic", "エスパー", "✨", "ゆびをふる",
     "あらゆる わざを つかうと いわれる まぼろしの ポケモン！",
     "ゆびをふる！ きよらかな こころを もつ トレーナーの まえに あらわれるロト！"),
    (6, 143, "カビゴン", "SSR", "normal", "ノーマル", "💤", "キョダイサイセイ",
     "1にちに 400キロの たべものを ぺろりと たいらげて ぐっすり おひるね！",
     "のしかかり！ おなかいっぱい たべたら どこでも ぐっすり ねむっちゃうロト！"),
    (7, 94, "ゲンガー", "SSR", "ghost", "ゴースト", "👻", "シャドーボール",
     "かげの なかに そっと かくれて みんなを おどろかせる いたずらっこ！",
     "シャドーボール！ くらやみから ニヤリと わらって おどろかせるのが だいすきロト！"),
    (8, 149, "カイリュー", "SSR", "dragon", "ドラゴン", "🐉", "はかいこうせん",
     "ちきゅうを たった 16じかんで 1しゅう してしまう やさしい うみの けしん！",
     "はかいこうせん！ おおぞらを マッハの スピードで とびまわる やさしい ドラゴンロト！"),
    (9, 3, "フシギバナ", "SSR", "grass", "くさ", "🌺", "ハードプラント",
     "せなかの おおきな はなに たいようの ひかりを あつめて パワーに かえる！",
     "ハードプラント！ せなかの おおきな はなから あまい かおりが ただようロト！"),
    (10, 9, "カメックス", "SSR", "water", "みず", "🌊", "ハイドロカノン",
     "こうらの ロケットほうから ぶあつい てっぱんも つらぬく すいりゅうを はっしゃ！",
     "ハイドロカノン！ こうらの ふんしゃこうから ちょうきょうりょくな みずを うつロト！"),
    (11, 130, "ギャラドス", "SR", "water", "みず・ひこう", "🌊", "たきのぼり",
     "コイキングから だいしんか！ あれくるう うみを こえる だいはくりょく！",
     "たきのぼり！ おおきな からだで うみの あらしも なんのそのロト！"),
    (12, 131, "ラプラス", "SR", "ice", "みず・こおり", "❄️", "れいとうビーム",
     "ひとや ポケモンを せなかに のせて うみを わたるのが だいすきな やさしい ポケモン！",
     "れいとうビーム！ せなかに みんなを のせて ごきげんに うみを およぐロト！"),
    (13, 39, "プリン", "SR", "fairy", "フェアリー", "🎤", "うたう",
     "つぶらな ひとみを ゆらして ここちよい こもりうたを うたうよ！",
     "うたう！ プリンの うたを きくと だれでも ぐっすり ねむくなっちゃうロト！"),
    (14, 132, "メタモン", "SR", "normal", "ノーマル", "🟣", "へんしん",
     "ぜんしんの さいぼうを くみかえて みたもの なんにでも そっくり へんしん！",
     "へんしん！ どんな ポケモンにも そっくり そのまま へんしん できちゃうロト！"),
    (15, 54, "コダック", "SR", "water", "みず", "🦆", "ねんりき",
     "いつも あたまを かかえているけれど ときどき ふしぎな だいパワーを はっき！",
     "ねんりき！ あたまが いたくなると とつぜん すごい ちからが あふれだすロト！"),

    # I列 (16-30): イーブイフレンズ＆ジョウト・ホウエン伝説＆人気スター
    (16, 197, "ブラッキー", "SSR", "dark", "あく", "🌙", "あくのはどう",
     "まんげつの よるに からだの わっかが こがねいろに かがやく つきの ポケモン！",
     "あくのはどう！ まんげつの ひかりを あびると わっかの もようが かがやくロト！"),
    (17, 700, "ニンフィア", "SSR", "fairy", "フェアリー", "🎀", "ムーンフォース",
     "リボンの ような しょっかくから こころを いやす やさしい はどうを おくるよ！",
     "ムーンフォース！ だいすきな トレーナーの うでに リボンを まきつけて あるくロト！"),
    (18, 196, "エーフィ", "SR", "psychic", "エスパー", "☀️", "サイコキネシス",
     "たいようの ひかりを あびて ひたいの たまが キラリと ひかる！",
     "サイコキネシス！ ぜんしんの こまかい けで かぜの ながれを よみとるロト！"),
    (19, 134, "シャワーズ", "SR", "water", "みず", "💧", "なみのり",
     "みずの なかに とけこむ ように およぐ うつくしい みずの しんかポケモン！",
     "なみのり！ みずの なかに とけるように すがたを かくして およげるロト！"),
    (20, 135, "サンダース", "SR", "electric", "でんき", "⚡", "かみなり",
     "ぜんしんの けを ハリの ように さかだてて いなずまを うちだす！",
     "かみなり！ いちまんボルトの でんきを ぜんしんに ためこんで はっしゃするロト！"),
    (21, 136, "ブースター", "SR", "fire", "ほのお", "🔥", "フレアドライブ",
     "からだの なかの ほのおぶくろで 1700どの ほのおを もえあがらせる！",
     "フレアドライブ！ ふかふかの けなみと あつい ほのおが じまんロト！"),
    (22, 471, "グレイシア", "SR", "ice", "こおり", "❄️", "ふぶき",
     "まわりの くうきを いっしゅんで こおらせて ダイヤモンドダストを ふらせる！",
     "ふぶき！ キラキラ 輝く こおりの つぶを まわりに ふらせるロト！"),
    (23, 470, "リーフィア", "SR", "grass", "くさ", "🍃", "リーフブレード",
     "きれいな くうきを つくりだす しょくぶつの ような やさしい ポケモン！",
     "リーフブレード！ たいようの ひかりを あびて すきとおった くうきを つくるロト！"),
    (24, 249, "ルギア", "UR", "psychic", "エスパー・ひこう", "🌊", "エアロブラスト",
     "かるく はばたくだけで あらしを おこす うみの かみさまと よばれる でんせつ！",
     "エアロブラスト！ ふかい うみの そこで しずかに ちからを たくわえる でんせつロト！"),
    (25, 250, "ホウオウ", "UR", "fire", "ほのお・ひこう", "🌈", "せいなるほのお",
     "なないろに かがやく つばさで せかいを とび みたひとに しあわせを もたらす！",
     "せいなるほのお！ とんだ あとの そらには うつくしい にじが かかるロト！"),
    (26, 245, "スイクン", "SSR", "water", "みず", "💎", "オーロラビーム",
     "きたかぜの うまれかわり！ よごれた みずを いっしゅんで きよめる ちからを もつ！",
     "オーロラビーム！ だいちを かけめぐり みずを きれいに きよめる でんせつロト！"),
    (27, 248, "バンギラス", "SSR", "dark", "いわ・あく", "⛰️", "ストーンエッジ",
     "どんな こうげきも はねかえす よろいの からだで やまの かたちも かえてしまう！",
     "ストーンエッジ！ あるくだけで おおきな やまが ゆれるほどの パワーロト！"),
    (28, 384, "レックウザ", "UR", "dragon", "ドラゴン・ひこう", "☄️", "ガリョウテンセイ",
     "はるか じょうくうの オゾンそうを とびつづける てんくうの はしゃ！",
     "ガリョウテンセイ！ くもの はるか うえから ちじょうを みまもる てんくうの はしゃロト！"),
    (29, 282, "サーナイト", "SSR", "fairy", "フェアリー", "💖", "マジカルシャイン",
     "だいじな トレーナーを まもるため サイコパワーを ぜんかいに する！",
     "マジカルシャイン！ みらいを よちする ちからで トレーナーを まもりぬくロト！"),
    (30, 385, "ジラーチ", "SSR", "psychic", "はがね・エスパー", "🌟", "はめつのねがい",
     "1000ねんに 7にちだけ めを さまし どんな ねがいごとも かなえてくれる！",
     "ねがいごと！ たんざくに かいた みんなの ゆめを かなえる まぼろしの ポケモンロト！"),

    # N列 (31-45): シンオウ・イッシュ・カロス英雄＆人気スター
    (31, 448, "ルカリオ", "UR", "fighting", "かくとう・はがね", "🌀", "はどうだん",
     "すべての ものが はっする はどうを キャッチして ともに たたかう ゆうしゃ！",
     "はどうだん！ あいての こころと はどうを よみとる かくとうの エースロト！"),
    (32, 445, "ガブリアス", "UR", "dragon", "ドラゴン・じめん", "🦈", "ドラゴンダイブ",
     "ジェットきに まけない スピードで そらを かけぬける チャンピオンの エース！",
     "ドラゴンダイブ！ おんそくの スピードで えものを けっして のがさないロト！"),
    (33, 393, "ポッチャマ", "SSR", "water", "みず", "🐧", "バブルこうせん",
     "プライドが たかくて むねを はって あるく すがたが とっても キュート！",
     "バブルこうせん！ ころんでも すぐに むねを はって たちあがる がんばりやロト！"),
    (34, 493, "アルセウス", "UR", "legend", "ノーマル", "👑", "さばきのつぶて",
     "せかいの すべてを うみだしたと しんわに かたられる そうぞうの ポケモン！",
     "さばきのつぶて！ 宇宙と 世界の はじまりを つくったと いわれる しんわの ポケモンロト！"),
    (35, 483, "ディアルガ", "UR", "dragon", "はがね・ドラゴン", "⏳", "ときのほうこう",
     "じかんの ながれを じざいに あやつる ちからを もつ シンオウの でんせつ！",
     "ときのほうこう！ むねの ダイヤモンドが かがやくとき じかんが うごきだすロト！"),
    (36, 484, "パルキア", "UR", "water", "みず・ドラゴン", "🌌", "あくうせつだん",
     "くうかんの つながりを あやつり とおくの ばしょへも いっしゅんで いどうする！",
     "あくうせつだん！ ひろい くうかんを ゆがめる すごすぎる パワーの もちぬしロト！"),
    (37, 487, "ギラティナ", "UR", "ghost", "ゴースト・ドラゴン", "🌑", "シャドーダイブ",
     "このよの うらがわに ある やぶれたせかいに すむ でんせつの ドラゴン！",
     "シャドーダイブ！ かげの なかから いっしゅんで あらわれる でんせつの ポケモンロト！"),
    (38, 491, "ダークライ", "SSR", "dark", "あく", "🌘", "ダークホール",
     "しんげつの よるに あらわれ ふしぎな ゆめの せかいへ いざなう まぼろし！",
     "ダークホール！ くらやみの なかで あおい ひとみが クールに ひかるロト！"),
    (39, 571, "ゾロアーク", "SSR", "dark", "あく", "🦊", "ナイトバースト",
     "まぼろしの けしきを みせる イリュージョンで なかまを しっかり まもりぬく！",
     "イリュージョン！ そっくりな まぼろしを みせて あいてを あっと おどろかせるロト！"),
    (40, 643, "レシラム", "SSR", "fire", "ドラゴン・ほのお", "🤍", "あおいほのお",
     "しっぽの エンジンから ふきだす ほのおで せかいの てんきも かえてしまう！",
     "あおいほのお！ しんじつを もとめる ひとを たすける まっしろな でんせつドラゴンロト！"),
    (41, 644, "ゼクロム", "SSR", "electric", "ドラゴン・でんき", "⚡", "らいげき",
     "かみなりぐもに みを かくし イッシュの そらを かけめぐる こくえんの ドラゴン！",
     "らいげき！ いなずまを まとって おおぞらを つらぬく でんせつの ドラゴンロト！"),
    (42, 658, "ゲッコウガ", "UR", "water", "みず・あく", "🥷", "みずしゅりけん",
     "にんじゃの ように しゅつぼつ じざい！ みずを かためた しゅりけんを なげる！",
     "みずしゅりけん！ にんじゃのような ちょうスピードで かけまわる クールな エースロト！"),
    (43, 702, "デデンネ", "SR", "electric", "でんき・フェアリー", "🐹", "ほっぺすりすり",
     "ヒゲの アンテナから でんぱを とばして とおくの なかまと おはなしするよ！",
     "ほっぺすりすり！ まるい からだと ヒゲの アンテナが とっても かわいいロト！"),
    (44, 373, "ボーマンダ", "SR", "dragon", "ドラゴン・ひこう", "🐲", "そらをとぶ",
     "つよく ねがいづづけた けっか みごとな あかい つばさが はえてきた ドラゴン！",
     "そらをとぶ！ おおきな あかい つばさで うれしそうに おおぞらを まいあがるロト！"),
    (45, 376, "メタグロス", "SSR", "psychic", "はがね・エスパー", "🤖", "コメットパンチ",
     "スーパーコンピュータよりも はやい ずのうと こうてつの ボディを もつ！",
     "コメットパンチ！ 4つの ずのうで どんな けいさんも いっしゅんで とくロト！"),

    # G列 (46-60): アローラ・ガラル大人気スター
    (46, 778, "ミミッキュ", "UR", "ghost", "ゴースト・フェアリー", "🧸", "じゃれつく",
     "みんなと なかよく なりたくて ピカチュウに にせた ぬのを かぶっているよ！",
     "じゃれつく！ みんなと ともだちに なりたくて ぬのに おかおを かいたんだロト！"),
    (47, 722, "モクロー", "SSR", "grass", "くさ・ひこう", "🦉", "このは",
     "おとも たてずに そらを とび くるっと くびを まわして こちらを みるよ！",
     "このは！ まんまる ボディと ちょうネクタイみたいな はっぱが かわいいロト！"),
    (48, 725, "ニャビー", "SR", "fire", "ほのお", "🐱", "ひのこ",
     "クールに みえるけれど なかまおもい！ おなかの けだまを もやして ひを ふく！",
     "ひのこ！ なつくと ゴロゴロ あまえてくれる ほのおの こねこポケモンロト！"),
    (49, 728, "アシマリ", "SR", "water", "みず", "🦭", "うたかたのアリア",
     "おはなで おおきな みずの バルーンを つくって ステージみたいに あそぶよ！",
     "うたかたのアリア！ まいにち バルーンづくりの れんしゅうを がんばっているロト！"),
    (50, 791, "ソルガレオ", "UR", "fire", "エスパー・はがね", "🦁", "メテオドライブ",
     "たいようを くらいつくす けもの！ ぜんしんから まぶしい ひかりを はなつ！",
     "メテオドライブ！ よるでも まひるのように まぶしく かがやく たいようの ししロト！"),
    (51, 792, "ルナアーラ", "UR", "ghost", "エスパー・ゴースト", "🦇", "シャドーレイ",
     "つきを さそう けもの！ ほしぞらのように きらめく おおきな つばさを ひろげる！",
     "シャドーレイ！ まんげつの ように うつくしく ひかる よぞらの でんせつロト！"),
    (52, 807, "ゼラオラ", "SSR", "electric", "でんき", "⚡", "プラズマフィスト",
     "カミナリが おちるのと おなじ はやさで かけぬける まぼろしの ポケモン！",
     "プラズマフィスト！ あおしろい いなずまを まとって こうそくで かけぬけるロト！"),
    (53, 815, "エースバーン", "UR", "fire", "ほのお", "⚽", "かえんボール",
     "こいしを リフティングして しゃくねつの サッカーボールを ゴールへ シュート！",
     "かえんボール！ どんな ピンチでも ゴールを きめる ほのおの ストライカーロト！"),
    (54, 835, "ワンパチ", "SR", "electric", "でんき", "🐶", "ほっぺすりすり",
     "はしるとき パチパチと でんきを うみだす げんきいっぱいの こいぬポケモン！",
     "スパーク！ おやつが だいすきで しっぽを ふりながら パチパチ はしるロト！"),
    (55, 887, "ドラパルト", "SSR", "ghost", "ドラゴン・ゴースト", "🚀", "ドラゴンアロー",
     "ツノの あなに ドラメシヤを のせて マッハの スピードで うちだすよ！",
     "ドラゴンアロー！ ドラメシヤたちと いっしょに おおぞらを こうそく ひこうするロト！"),
    (56, 888, "ザシアン", "UR", "fairy", "フェアリー・はがね", "🗡️", "きょじゅうざん",
     "かがやく けんを くわえて どんな きょだいな てきも いっとうりょうだん！",
     "きょじゅうざん！ ガラルを すくった でんせつの けんと ともに まいおどるロト！"),
    (57, 889, "ザマゼンタ", "SSR", "fighting", "かくとう・はがね", "🛡️", "きょじゅうだん",
     "こがねの たてで どんな こうげきも はじきかえす たのもしい おうの ポケモン！",
     "きょじゅうだん！ かがやく よろいの たてで なかまを てっぺき ガードするロト！"),
    (58, 890, "ムゲンダイナ", "UR", "dragon", "どく・ドラゴン", "☄️", "ダイマックスほう",
     "むげんの ダイマックス エネルギーを むねの コアに やどす ちょうきょだいポケモン！",
     "ダイマックスほう！ そらを あかく そめるほどの むげんパワーを はなつロト！"),
    (59, 892, "ウーラオス", "SSR", "fighting", "かくとう", "🥋", "あんこくきょうだ",
     "きたえぬかれた わざで いちげき ひっさつ！ かくとうどうを きわめた たつじん！",
     "あんこくきょうだ！ しゅぎょうを かさねて さいきょうの けんぽうを みに つけたロト！"),
    (60, 172, "ピチュー", "SR", "electric", "でんき", "⚡", "ボルテッカー",
     "なかまと しっぽの さきを あわせて パチパチと ひばなを とばして あそぶよ！",
     "でんきショック！ うれしいと パチパチ でんきが あふれちゃう げんきっ子ロト！"),

    # O列 (61-75): パルデア最新スター＆歴代御三家オールスター
    (61, 906, "ニャオハ", "SSR", "grass", "くさ", "🌿", "トリックフラワー",
     "ふみふみ すると あまい アロマが ひろがる きまぐれで かわいい くさねこ！",
     "このは！ まえあしで ふみふみ すると いい かおりが ふわふわ ひろがるロト！"),
    (62, 909, "ホゲータ", "SSR", "fire", "ほのお", "🍎", "フレアソング",
     "たべることが だいすきで のんびりやさん！ うたいながら ほのおを はなつ！",
     "フレアソング！ ごきげんに うたを うたいながら ほのおパワーが アップするロト！"),
    (63, 912, "クワッス", "SSR", "water", "みず", "🧢", "アクアステップ",
     "つやつやの あたまの はねを いつも きれいに ととのえる ダンスの めいしゅ！",
     "アクアステップ！ かろやかな ステップで リズムに のって おどりだすロト！"),
    (64, 1007, "コライドン", "UR", "fighting", "かくとう・ドラゴン", "❤️‍🔥", "アクセルブレイク",
     "だいちを くだく きょうりょくな キックと つばさで かけぬける こだいの おう！",
     "アクセルブレイク！ すごい ジャンプりょくと パワーで ぼうけんを リードするロト！"),
    (65, 1008, "ミライドン", "UR", "electric", "でんき・ドラゴン", "⚡", "イナズマドライブ",
     "いなずまの ジェットで みらいの ように こうそく ドライブする でんせつ！",
     "イナズマドライブ！ でんげきを まきちらしながら ひかりの はやさで はしるロト！"),
    (66, 959, "デカヌチャン", "SSR", "fairy", "フェアリー・はがね", "🔨", "デカハンマー",
     "ちいさな からだで 100キロの きょだいハンマーを ぶんぶん ふりまわす！",
     "デカハンマー！ じぶんより おおきな ハンマーを かるがると ふりまわすロト！"),
    (67, 921, "パモ", "SR", "electric", "でんき", "🧡", "ほっぺすりすり",
     "ふわふわの ほっぺと てのひらで でんきを つくる もふもふ ポケモン！",
     "ほっぺすりすり！ ほっぺを なでなで して でんきを じゅうでん するロト！"),
    (68, 26, "ライチュウ", "SR", "electric", "でんき", "⚡", "10まんボルト",
     "ながい しっぽを じめんに たてて でんきを にがしながら 10まんボルトを はなつ！",
     "ボルテッカー！ ピカチュウから しんかした たのもしい でんきポケモンロト！"),
    (69, 937, "ソウブレイズ", "UR", "ghost", "ほのお・ゴースト", "⚔️", "むねんのつるぎ",
     "りょううでの ほのおの だいけんで どんな ものも きりさく ほのおの きし！",
     "むねんのつるぎ！ あおく もえる ほのおの ブレードが ちょうクールロト！"),
    (70, 936, "グレンアルマ", "SSR", "fire", "ほのお・エスパー", "🛡️", "アーマーキャノン",
     "あかい よろいを ひとつに あわせて しゃくねつの キャノンほうを はっしゃ！",
     "アーマーキャノン！ せいぎかん あふれる ほのおの せんしポケモンロト！"),
    (71, 1024, "テラパゴス", "UR", "legend", "ノーマル", "💎", "テラクラスター",
     "こうらの ジュエルが なないろに きらめく テラスタルの ひみつを にぎる ポケモン！",
     "テラクラスター！ ほうせきのように キラキラ かがやく でんせつの ポケモンロト！"),
    (72, 1017, "オーガポン", "UR", "grass", "くさ", "🎭", "ツタこんぼう",
     "キラキラの おめんを かぶって おどりだす こうきしん いっぱいの ポケモン！",
     "ツタこんぼう！ おめんを かえると いろんな タイプの ちからが あふれるロト！"),
    (73, 4, "ヒトカゲ", "SR", "fire", "ほのお", "🔥", "かえんほうしゃ",
     "しっぽの ほのおは げんきの しるし！ うれしいときは ゆらゆら ゆれるよ！",
     "かえんほうしゃ！ しっぽの ほのおを パチパチ もやして げんきいっぱいロト！"),
    (74, 7, "ゼニガメ", "SR", "water", "みず", "🐢", "みずでっぽう",
     "まるい こうらに ひっこんで いきおいよく みずでっぽうを はっしゃ！",
     "みずでっぽう！ なかまと いっしょに みずあそび するのが だいすきロト！"),
    (75, 1, "フシギダネ", "SR", "grass", "くさ", "🌱", "つるのムチ",
     "うまれたときから せなかに ある タネと いっしょに すくすく そだつよ！",
     "つるのムチ！ ひなたぼっこを すると せなかの タネが おおきく そだつロト！"),
]

# Extra 45 iconic crowd Pokemon for "Where's Wally?" (sagase) so we have 120 distinct species!
EXTRA_CROWD = [
    (52, "ニャース"), (202, "ソーナンス"), (129, "コイキング"), (79, "ヤドン"),
    (37, "ロコン"), (58, "ガーディ"), (68, "カイリキー"), (251, "セレビィ"),
    (494, "ビクティニ"), (492, "シェイミ"), (816, "メッソン"), (810, "サルノリ"),
    (813, "ヒバニー"), (255, "アチャモ"), (258, "ミズゴロウ"), (252, "キモリ"),
    (152, "チコリータ"), (155, "ヒノアラシ"), (158, "ワニノコ"), (447, "リオル"),
    (311, "プラスル"), (312, "マイナン"), (175, "トゲピー"), (183, "マリル"),
    (446, "ゴンベ"), (194, "ウパー"), (980, "ドオー"), (978, "シャリタツ"),
    (50, "ディグダ"), (43, "ナゾノクサ"), (25, "ピカチュウ"), (133, "イーブイ"),
    (390, "ヒコザル"), (387, "ナエトル"), (495, "ツタージャ"), (498, "ポカブ"),
    (501, "ミジュマル"), (650, "ハリマロン"), (653, "フォッコ"), (656, "ケロマツ"),
    (759, "ヌイコグマ"), (777, "トゲデマル"), (872, "ユキハミ"), (926, "パピモッチ"),
    (100, "ビリリダマ"), (35, "ピッピ"), (113, "ラッキー"),
]

# Deduplicate extra crowd against MAIN_75 dex_ids
main_dex_set = {row[1] for row in MAIN_75}
EXTRA_UNIQUE = []
for dex_id, nm in EXTRA_CROWD:
    if dex_id not in main_dex_set and all(x[0] != dex_id for x in EXTRA_UNIQUE):
        EXTRA_UNIQUE.append((dex_id, nm))

# Shiny targets for "Where's Wally?" bonus!
SHINY_LIST = [
    (129, "きんの コイキング"),
    (6, "くろい リザードン"),
    (151, "あおい ミュウ"),
    (133, "ぎんの イーブイ"),
    (197, "あおいわっかの ブラッキー"),
    (384, "くろい レックウザ"),
    (700, "みずいろ ニンフィア"),
    (132, "みずいろ メタモン"),
]

# Elemental TCG Card Palettes: (top_rgb, mid_rgb, bot_rgb, glow_rgb)
TYPE_PALETTES = {
    "electric": ((253, 224, 71), (245, 158, 11), (180, 83, 9), (254, 249, 195)),
    "fire":     ((251, 146, 60), (220, 38, 38), (127, 29, 29), (254, 215, 170)),
    "water":    ((56, 189, 248), (37, 99, 235), (30, 58, 138), (186, 230, 253)),
    "grass":    ((74, 222, 128), (22, 163, 74), (20, 83, 45), (187, 247, 208)),
    "psychic":  ((232, 121, 249), (147, 51, 234), (76, 29, 149), (245, 208, 254)),
    "ghost":    ((167, 139, 250), (109, 40, 217), (46, 16, 101), (221, 214, 254)),
    "dragon":   ((99, 102, 241), (67, 56, 202), (17, 24, 39), (199, 210, 254)),
    "fairy":    ((249, 168, 212), (236, 72, 153), (131, 24, 67), (252, 231, 243)),
    "dark":     ((148, 163, 184), (51, 65, 85), (15, 23, 42), (226, 232, 240)),
    "ice":      ((165, 243, 252), (6, 182, 212), (22, 78, 99), (207, 250, 254)),
    "fighting": ((251, 113, 133), (225, 29, 72), (136, 19, 55), (254, 205, 211)),
    "normal":   ((253, 230, 138), (217, 119, 6), (120, 53, 15), (254, 243, 199)),
    "legend":   ((253, 224, 71), (168, 85, 247), (30, 58, 138), (255, 255, 255)),
}

SESSION = requests.Session()

def fetch_cached(url, cache_name):
    p = os.path.join(RAW_CACHE, cache_name)
    if os.path.exists(p) and os.path.getsize(p) > 200:
        with open(p, "rb") as f:
            return f.read()
    for attempt in range(4):
        r = SESSION.get(url, timeout=20)
        if r.status_code == 200 and len(r.content) > 200:
            with open(p, "wb") as f:
                f.write(r.content)
            return r.content
    raise RuntimeError(f"Failed to download {url} (status={r.status_code})")

def render_tcg_card_bg(size, type_key, seed=0):
    rng = random.Random(seed)
    top_c, mid_c, bot_c, glow_c = TYPE_PALETTES.get(type_key, TYPE_PALETTES["normal"])
    y = np.linspace(0, 1, size)[:, None]
    x = np.linspace(0, 1, size)[None, :]

    # Smooth 3-stop gradient + radial center burst
    c1 = np.array(top_c, dtype=np.float32)
    c2 = np.array(mid_c, dtype=np.float32)
    c3 = np.array(bot_c, dtype=np.float32)
    cg = np.array(glow_c, dtype=np.float32)

    upper = y < 0.5
    t_up = (y * 2.0)[..., None]
    t_dn = ((y - 0.5) * 2.0)[..., None]
    grad = np.where(upper[..., None], c1 * (1 - t_up) + c2 * t_up, c2 * (1 - t_dn) + c3 * t_dn)

    # Conic anime burst rays from center
    dx = x - 0.5
    dy = y - 0.46
    dist = np.sqrt(dx * dx + dy * dy)
    angle = np.arctan2(dy, dx)
    rays = (np.sin(angle * 16.0 + seed) * 0.5 + 0.5) ** 2.2
    radial = np.clip(1.0 - dist * 1.45, 0.0, 1.0)

    mix = np.clip(radial * 0.62 + rays * radial * 0.25, 0.0, 0.85)[..., None]
    arr = np.clip(grad * (1.0 - mix) + cg * mix, 0, 255).astype(np.uint8)
    bg = Image.fromarray(arr, mode="RGB").convert("RGBA")

    # Add glowing Pokeball-inspired aura rings & sparkles
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = size // 2, int(size * 0.47)
    r_outer = int(size * 0.37)
    r_inner = int(size * 0.26)
    draw.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer), outline=(*glow_c, 95), width=max(2, size // 95))
    draw.ellipse((cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner), outline=(255, 255, 255, 85), width=max(2, size // 120))

    for _ in range(18):
        sx = rng.randint(12, size - 12)
        sy = rng.randint(12, size - 12)
        sr = rng.randint(2, max(4, size // 60))
        draw.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(255, 255, 255, rng.randint(110, 220)))

    return Image.alpha_composite(bg, overlay)

def trim_and_pad_rgba(raw_png_bytes, out_size=260, add_shadow=True):
    im = Image.open(io.BytesIO(raw_png_bytes)).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    target = int(out_size * 0.88)
    scale = min(target / max(1, w), target / max(1, h))
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (out_size, out_size), (0, 0, 0, 0))
    ox = (out_size - nw) // 2
    oy = (out_size - nh) // 2

    if add_shadow:
        alpha = resized.split()[3]
        shadow = Image.new("RGBA", (nw, nh), (0, 0, 0, 155))
        shadow.putalpha(alpha.point(lambda a: int(a * 0.55)))
        sh_canvas = Image.new("RGBA", (out_size, out_size), (0, 0, 0, 0))
        sh_canvas.paste(shadow, (ox, min(out_size - nh, oy + max(3, out_size // 50))))
        sh_canvas = sh_canvas.filter(ImageFilter.GaussianBlur(radius=max(2, out_size // 48)))
        canvas = Image.alpha_composite(canvas, sh_canvas)

    canvas.paste(resized, (ox, oy), resized)
    return canvas

def composite_card(raw_png_bytes, type_key, size=340, seed=0):
    bg = render_tcg_card_bg(size, type_key, seed=seed)
    sprite = trim_and_pad_rgba(raw_png_bytes, out_size=int(size * 0.92), add_shadow=True)
    # White sticker rim glow around Pokemon for ultra-pop readability!
    alpha = sprite.split()[3]
    rim_alpha = alpha.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2.2))
    rim = Image.new("RGBA", sprite.size, (255, 255, 255, 255))
    rim.putalpha(rim_alpha.point(lambda a: min(230, int(a * 0.85))))

    ox = (size - sprite.width) // 2
    oy = int((size - sprite.height) * 0.38)
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    layer.paste(rim, (ox, oy), rim)
    layer.paste(sprite, (ox, oy), sprite)
    return Image.alpha_composite(bg, layer).convert("RGB")

def draw_pokeball_card_art(size=360, is_master=False):
    bg = render_tcg_card_bg(size, "legend" if is_master else "fire", seed=777)
    ov = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cx, cy = size // 2, size // 2
    r = int(size * 0.34)
    # Shadow
    d.ellipse((cx - r + 4, cy - r + 8, cx + r + 4, cy + r + 8), fill=(0, 0, 0, 130))
    # Bottom white half
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(248, 250, 252, 255), outline=(20, 20, 25, 255), width=max(6, size // 36))
    # Top half (Red for Pokeball, Purple for Masterball)
    top_col = (147, 51, 234, 255) if is_master else (239, 68, 68, 255)
    d.pieslice((cx - r, cy - r, cx + r, cy + r), start=180, end=360, fill=top_col, outline=(20, 20, 25, 255), width=max(6, size // 36))
    if is_master:
        pr = int(r * 0.34)
        d.ellipse((cx - int(r * 0.68), cy - int(r * 0.82), cx - int(r * 0.12), cy - int(r * 0.28)), fill=(236, 72, 153, 255), outline=(20, 20, 25, 255), width=4)
        d.ellipse((cx + int(r * 0.12), cy - int(r * 0.82), cx + int(r * 0.68), cy - int(r * 0.28)), fill=(236, 72, 153, 255), outline=(20, 20, 25, 255), width=4)
    # Center band & button
    bw = max(8, size // 26)
    d.line((cx - r + 3, cy, cx + r - 3, cy), fill=(20, 20, 25, 255), width=bw)
    br = int(r * 0.28)
    d.ellipse((cx - br, cy - br, cx + br, cy + br), fill=(255, 255, 255, 255), outline=(20, 20, 25, 255), width=max(5, size // 42))
    ibr = int(br * 0.56)
    d.ellipse((cx - ibr, cy - ibr, cx + ibr, cy + ibr), fill=(254, 240, 138, 255), outline=(202, 138, 4, 255), width=3)
    # Gloss highlight
    d.ellipse((cx - int(r * 0.55), cy - int(r * 0.72), cx - int(r * 0.15), cy - int(r * 0.42)), fill=(255, 255, 255, 135))
    return Image.alpha_composite(bg, ov).convert("RGB")

def convert_ogg_to_mp3(ogg_bytes, mp3_path):
    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 500:
        return
    tmp_ogg = mp3_path + ".tmp.ogg"
    with open(tmp_ogg, "wb") as f:
        f.write(ogg_bytes)
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", tmp_ogg,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=0.08",
            "-ar", "24000", "-ac", "1", "-b:a", "56k", mp3_path
        ],
        check=True
    )
    os.remove(tmp_ogg)

LEADER_MAP = {
    "pikachu": 1,
    "charizard": 2,
    "eevee": 3,
    "mewtwo": 4,
    "mew": 5,
    "lucario": 31,
    "greninja": 42,
    "rayquaza": 28,
    "sylveon": 17,
    "gengar": 7,
    "mimikyu": 46,
    "piplup": 33,
}

def process_main_pokemon(row):
    bid, dex_id, name, rarity, type_key, type_label, emoji, move, quote, spoken_quote = row
    art_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{dex_id}.png"
    cry_url = f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/{dex_id}.ogg"

    png_bytes = fetch_cached(art_url, f"art_{dex_id}.png")
    ogg_bytes = fetch_cached(cry_url, f"cry_{dex_id}.ogg")

    # 1. TCG Holographic Card Portrait (340x340 WebP)
    card_img = composite_card(png_bytes, type_key, size=340, seed=bid * 17)
    card_img.save(os.path.join(CARDS_DIR, f"poke_{bid:02d}.webp"), "WEBP", quality=86, method=6)

    # 2. Clean Transparent Sprite with soft drop shadow (240x240 WebP) for Sagase / Sugoroku / UI
    sp_img = trim_and_pad_rgba(png_bytes, out_size=240, add_shadow=True)
    sp_img.save(os.path.join(SPRITES_DIR, f"dex_{dex_id}.webp"), "WEBP", quality=86, method=6)

    # 3. Official Pokemon Cry MP3 (for iPad/iOS/Android/PC)
    convert_ogg_to_mp3(ogg_bytes, os.path.join(CRIES_DIR, f"dex_{dex_id}.mp3"))
    return bid

def process_extra_pokemon(item):
    dex_id, name = item
    art_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{dex_id}.png"
    cry_url = f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/{dex_id}.ogg"
    png_bytes = fetch_cached(art_url, f"art_{dex_id}.png")
    ogg_bytes = fetch_cached(cry_url, f"cry_{dex_id}.ogg")

    sp_img = trim_and_pad_rgba(png_bytes, out_size=220, add_shadow=True)
    sp_img.save(os.path.join(SPRITES_DIR, f"dex_{dex_id}.webp"), "WEBP", quality=85, method=6)
    convert_ogg_to_mp3(ogg_bytes, os.path.join(CRIES_DIR, f"dex_{dex_id}.mp3"))
    return dex_id

def process_shiny_pokemon(item):
    dex_id, name = item
    shiny_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/{dex_id}.png"
    png_bytes = fetch_cached(shiny_url, f"shiny_{dex_id}.png")
    sp_img = trim_and_pad_rgba(png_bytes, out_size=240, add_shadow=True)
    sp_img.save(os.path.join(SPRITES_DIR, f"shiny_{dex_id}.webp"), "WEBP", quality=88, method=6)
    return dex_id

def main():
    print(f"Building 75 main Pokemon cards + sprites + cries...")
    with ThreadPoolExecutor(max_workers=10) as pool:
        futs = [pool.submit(process_main_pokemon, r) for r in MAIN_75]
        for i, fut in enumerate(as_completed(futs), 1):
            fut.result()
            if i % 15 == 0 or i == len(MAIN_75):
                print(f"  Main 75 progress: {i}/{len(MAIN_75)}", flush=True)

    print(f"Building {len(EXTRA_UNIQUE)} extra crowd Pokemon sprites + cries...")
    with ThreadPoolExecutor(max_workers=10) as pool:
        futs = [pool.submit(process_extra_pokemon, x) for x in EXTRA_UNIQUE]
        for i, fut in enumerate(as_completed(futs), 1):
            fut.result()
            if i % 15 == 0 or i == len(EXTRA_UNIQUE):
                print(f"  Extra crowd progress: {i}/{len(EXTRA_UNIQUE)}", flush=True)

    print(f"Building {len(SHINY_LIST)} shiny Pokemon bonus sprites...")
    with ThreadPoolExecutor(max_workers=8) as pool:
        for fut in as_completed([pool.submit(process_shiny_pokemon, s) for s in SHINY_LIST]):
            fut.result()

    # High-res 440x440 Leader Portraits + Free + Card Back
    print("Rendering 12 high-res Oshi Partner Leader cards + Pokeball/Masterball emblems...")
    row_by_bid = {r[0]: r for r in MAIN_75}
    for lid, bid in LEADER_MAP.items():
        r = row_by_bid[bid]
        png_bytes = fetch_cached(
            f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{r[1]}.png",
            f"art_{r[1]}.png"
        )
        hi = composite_card(png_bytes, r[4], size=440, seed=bid * 31)
        hi.save(os.path.join(CARDS_DIR, f"leader_{lid}.webp"), "WEBP", quality=88, method=6)

    draw_pokeball_card_art(360, is_master=True).save(os.path.join(CARDS_DIR, "free.webp"), "WEBP", quality=88, method=6)
    draw_pokeball_card_art(360, is_master=False).save(os.path.join(CARDS_DIR, "card_back.webp"), "WEBP", quality=88, method=6)

    # Export shared JS dataset for all 4 games!
    main_json = [
        {
            "id": r[0],
            "dexId": r[1],
            "name": r[2],
            "rarity": r[3],
            "typeKey": r[4],
            "attr": r[5],
            "emoji": r[6],
            "move": r[7],
            "quote": r[8],
            "spokenQuote": r[9],
            "cardImg": f"assets/cards/poke_{r[0]:02d}.webp",
            "spriteImg": f"assets/sprites/dex_{r[1]}.webp",
            "crySrc": f"assets/audio/cries/dex_{r[1]}.mp3",
        }
        for r in MAIN_75
    ]
    crowd_json = [
        {
            "dexId": r[1],
            "name": r[2],
            "typeKey": r[4],
            "spriteImg": f"assets/sprites/dex_{r[1]}.webp",
            "crySrc": f"assets/audio/cries/dex_{r[1]}.mp3",
            "isMain": True,
            "bingoId": r[0],
        }
        for r in MAIN_75
    ] + [
        {
            "dexId": dex_id,
            "name": nm,
            "typeKey": "normal",
            "spriteImg": f"assets/sprites/dex_{dex_id}.webp",
            "crySrc": f"assets/audio/cries/dex_{dex_id}.mp3",
            "isMain": False,
            "bingoId": None,
        }
        for dex_id, nm in EXTRA_UNIQUE
    ]
    shiny_json = [
        {
            "dexId": dex_id,
            "name": nm,
            "spriteImg": f"assets/sprites/shiny_{dex_id}.webp",
            "crySrc": f"assets/audio/cries/dex_{dex_id}.mp3",
        }
        for dex_id, nm in SHINY_LIST
    ]

    js_payload = (
        "// Auto-generated Pokemon Game Land Shared Database\n"
        f"window.POKEMON_MAIN_75 = {json.dumps(main_json, ensure_ascii=False, indent=2)};\n"
        f"window.POKEMON_ALL_CROWD = {json.dumps(crowd_json, ensure_ascii=False, indent=2)};\n"
        f"window.POKEMON_SHINY_BONUS = {json.dumps(shiny_json, ensure_ascii=False, indent=2)};\n"
    )
    with open(os.path.join(DATA_DIR, "pokemon_db.js"), "w", encoding="utf-8") as f:
        f.write(js_payload)

    print(f"DONE! Total distinct Pokemon species: {len(crowd_json)}, Shiny bonus: {len(shiny_json)}")

if __name__ == "__main__":
    main()
