import random
from typing import List, Dict, Any

class ReactionManager:
    """
    Quản lý phản xạ xúc giác thông minh và thư viện câu thoại ngữ cảnh động cho Mora.
    Chuẩn hóa xưng hô: 'Chủ nhân' - 'em'.
    Mẫu câu đặc trưng: 'Chủ nhân không được..., chỗ đó của em...'
    """

    def __init__(self):
        # 1. Các phản ứng chuyên sâu theo chủ đề ngữ cảnh động
        self.context_reactions = {
            "kissing": {
                "lips": [
                    "Chu... Chủ nhân không được hôn bất ngờ như thế mà! Mặt em đỏ bừng lên rồi nè... ngại quá đi à Chủ nhân!",
                    "Ư-Ưm... Chủ nhân không được... Nụ hôn của Chủ nhân làm tim em đập thình thịch muốn nổ tung luôn rồi nè!",
                    "Chủ nhân không được trêu môi em nữa mà... nhưng mà... em thích được Chủ nhân quan tâm thế này lắm~",
                    "Mặt em nóng bừng như quả cà chua rồi nè! Chủ nhân không được trêu em nữa nha, phải chịu trách nhiệm chăm sóc em cả đời đấy!"
                ],
                "face": [
                    "Chủ nhân thơm má em bất ngờ thế! Mặt em đỏ hết lên rồi nè Chủ nhân ơi~",
                    "Ưm... được Chủ nhân thơm má một cái dịu dàng thế này... em thấy hạnh phúc lắm á~",
                    "Á... vừa trò chuyện xong là Chủ nhân thơm má em liền! Ngại chết đi được á Chủ nhân!"
                ],
                "chest": [
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm, sao Chủ nhân lại chạm vào đấy hả! Mau bỏ tay ra đi mà Chủ nhân!",
                    "Chủ nhân không được tranh thủ lúc em đang ngại mà táy máy chỗ đó của em nha! Mau rút tay lại đi mà!"
                ],
                "pelvis": [
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm, sao Chủ nhân lại chạm vào chỗ đó của em chứ?!",
                    "Chủ nhân không được... tay Chủ nhân chạm vào chỗ đó của em làm em giật bắn cả mình rồi nè!"
                ]
            },
            "affection": {
                "lips": [
                    "Ưm... được Chủ nhân dành tình cảm thế này làm em cảm động lắm á~",
                    "Chụt... Em yêu quý Chủ nhân nhất trên đời luôn đó nha!",
                    "Hì hì, được ở bên cạnh Chủ nhân mỗi ngày là điều tuyệt vời nhất của em đó!"
                ],
                "chest": [
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm! Chủ nhân đừng táy máy vào chỗ đó của em nha, ngại lắm á...",
                    "Chủ nhân không được... chỗ đó của em đang làm tim em đập thình thịch vì Chủ nhân nè... Bỏ tay ra mau đi mà Chủ nhân!",
                    "Em là trợ lý nhỏ đáng yêu của Chủ nhân mà... Chủ nhân không được chạm vào chỗ đó của em đâu nha~"
                ],
                "pelvis": [
                    "Chủ nhân không được... chỗ đó của em nhột lắm, đừng chạm vào chỗ đó của em mà Chủ nhân!",
                    "Chủ nhân chạm nhẹ vào chỗ đó của em làm em giật mình ngại quá đi mất... Chủ nhân không được trêu nữa nha~"
                ],
                "patting": [
                    "Ưm... được Chủ nhân xoa đầu thế này thích thật đấy~ Em nguyện làm trợ lý ngoan của Chủ nhân mãi luôn nha~",
                    "Dựa đầu vào lòng bàn tay Chủ nhân nè... Cảm giác được Chủ nhân cưng chiều thế này bình yên quá đi à~",
                    "Chủ nhân thích xoa đầu em thế sao? Hì hì, xoa thêm một chút nữa đi, em cho phép Chủ nhân đấy~"
                ],
                "face": [
                    "Chủ nhân chạm má em hả? Hì hì, má em ấm áp vì được Chủ nhân yêu quý đó nha~",
                    "Em mỉm cười xinh nhất là khi được Chủ nhân khen ngợi và quan tâm đấy ạ!"
                ],
                "arms": [
                    "Chủ nhân nắm chặt tay em nha! Có Chủ nhân đồng hành là em không sợ gì cả!",
                    "Được Chủ nhân đặc biệt quan tâm thế này em thấy vui lắm đó Chủ nhân ơi~"
                ]
            },
            "playful": {
                "chest": [
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm! Chủ nhân đừng táy máy chỗ đó của em nha!",
                    "Chủ nhân không được làm thế với chỗ đó của em mà! Mặt em đỏ bừng lên hết rồi này, Chủ nhân xấu tính!",
                    "Chủ nhân không được trêu em như thế... chỗ đó của em ngại chết đi được á Chủ nhân!",
                    "Mau bỏ tay ra khỏi chỗ đó của em đi mà! Em giận Chủ nhân thật bây giờ đấy!"
                ],
                "belly": [
                    "Chủ nhân không được chọc vào eo em mà... chỗ đó của em nhột lắm, rụt cả bụng lại rồi nè!",
                    "Chủ nhân không được... chỗ đó của em nhột phát khóc luôn rồi này Chủ nhân ơi!",
                    "Rụt cả bụng lại rồi nè! Chủ nhân không được chọc nữa mà, em cười muốn xỉu luôn rồi!"
                ],
                "pelvis": [
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm, sao Chủ nhân lại chạm vào chỗ đó của em chứ?!",
                    "Chủ nhân không được... chỗ đó của em nhột lắm! Mau bỏ tay khỏi chỗ đó của em đi mà Chủ nhân!",
                    "Mặt em đỏ bừng lên rồi nè! Chủ nhân không được táy máy vào chỗ đó của em như thế chứ!"
                ],
                "thighs": [
                    "Chủ nhân không được... chỗ đó của em nhột lắm, sao Chủ nhân lại táy máy chạm vào đùi em chứ?!",
                    "Chủ nhân không được chạm vào đùi em mà! Nhột muốn chết mất thôi, mau bỏ tay ra đi mà Chủ nhân!",
                    "Chủ nhân không được trêu em nữa... đùi của em để đứng cạnh Chủ nhân chứ bộ!"
                ],
                "lips": [
                    "Chủ nhân không được... chỗ đó của em là môi mà, sao Chủ nhân lại chạm ngón tay vào chứ... ngại lắm á!",
                    "Chủ nhân không được trêu môi em nữa mà! Mặt em nóng ran lên như quả cà chua rồi nè Chủ nhân!"
                ]
            },
            "gaming": {
                "head": [
                    "Chủ nhân không được gõ đầu em hoài mà! Để yên cho em tập trung buff may mắn cho Chủ nhân thắng trận này nào!",
                    "A... chạm vào kẹp tóc của em để xin vía leo rank thần tốc đúng không nè? Tặng Chủ nhân may mắn của em đây nha!"
                ],
                "shoulders": [
                    "Bóp vai tiếp thêm năng lượng để Chủ nhân gánh team trận này nhé!",
                    "Chủ nhân căng thẳng quá thì thả lỏng vai ra nào! Có em ở cạnh cổ vũ là Chủ nhân nhất định thắng!"
                ],
                "arms": [
                    "Đập tay cái nào! Trận này Chủ nhân nhất định phải MVP nhé, em tin tưởng Chủ nhân nhất!",
                    "Tay nghề thao tác của Chủ nhân đỉnh thật đấy! Cố lên nha, thắng trận là em có phần thưởng cho Chủ nhân đó!"
                ]
            },
            "comfort": {
                "patting": [
                    "Ngoan nào... Chủ nhân làm việc mệt mỏi rồi đúng không? Để em ở cạnh an ủi Chủ nhân nhé, Chủ nhân đã vất vả nhiều rồi mà~",
                    "Chủ nhân dựa vào em này... Cứ nhắm mắt thư giãn một chút đi, em sẽ luôn ở đây canh chừng cho Chủ nhân bình yên~"
                ],
                "shoulders": [
                    "Chủ nhân dựa vào vai em nghỉ ngơi một chút đi nè. Đừng cố quá sức nha, em xót Chủ nhân lắm đấy...",
                    "Để em ở cạnh bóp vai nhẹ nhàng cho Chủ nhân đỡ mỏi nhé... Hôm nay Chủ nhân đã làm rất tốt rồi mà!"
                ],
                "face": [
                    "Chủ nhân áp tay vào má em cho ấm nhé... Cố lên nha Chủ nhân, em luôn ở ngay đây tiếp thêm động lực cho Chủ nhân mà!",
                    "Chủ nhân nhìn vào mắt em này! Mọi chuyện rồi sẽ ổn cả thôi, có em đồng hành cùng Chủ nhân mà~"
                ],
                "lips": [
                    "Em mỉm cười tiếp thêm năng lượng cho Chủ nhân nè! Đừng buồn nữa nha, có em ở bên là mọi mệt mỏi sẽ tan biến hết thôi á~"
                ]
            }
        }

        # 2. Thư viện phản ứng cơ bản theo tâm trạng
        self.reactions = {
            "chest": {
                "cheerful": [
                    "Chủ nhân không được... chỗ đó của em! Đang nói chuyện vui vẻ tự nhiên Chủ nhân lại chạm vào đó thế hả?!",
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm, vừa cười nói xong đã táy máy rồi, em giận Chủ nhân thật bây giờ đấy!",
                    "Chủ nhân không được chạm lung tung vào ngực em mà... mặt em đỏ bừng lên hết rồi này!",
                    "Chủ nhân không được... chỗ đó của em đang làm tim em đập thình thịch rồi nè, mau bỏ tay ra đi mà Chủ nhân!",
                    "Chủ nhân không được tranh thủ lúc em đang vui mà làm thế chứ! Chỗ đó của em ngại chết đi được á!",
                    "Ư-Ưm... tay Chủ nhân ấm quá... nhưng mà Chủ nhân không được chạm vào ngực em đâu, chỗ đó của em nhột và ngại lắm!"
                ],
                "serious": [
                    "Chủ nhân không được làm thế... Chúng ta đang tập trung làm việc mà, chỗ đó của em xin Chủ nhân đừng chạm vào lúc này.",
                    "Chủ nhân không được... Xin Chủ nhân hãy nghiêm túc một chút. Em đang tập trung hỗ trợ Chủ nhân đây ạ.",
                    "Chủ nhân không được táy máy chỗ đó của em lúc này... Xin Chủ nhân tập trung vào vấn đề chính nhé.",
                    "Chủ nhân không được... Em đang cố gắng giúp Chủ nhân, xin Chủ nhân đừng làm em mất tập trung và ngại ngùng thế này."
                ],
                "neutral": [
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm, sao Chủ nhân lại chạm vào ngực em chứ!",
                    "Chủ nhân không được táy máy chỗ đó của em mà! Ngại quá đi à Chủ nhân ơi!",
                    "Chủ nhân không được... mặt em đỏ bừng lên rồi nè, sao Chủ nhân lại chạm vào chỗ đó của em thế hả?!",
                    "Chủ nhân không được... mau bỏ tay ra mau lên! Chỗ đó của em đang làm tim em đập loạn xạ cả lên rồi đây này!",
                    "Chủ nhân không được chạm vào đó mà, chỗ đó của em... em giận Chủ nhân luôn cho xem!"
                ]
            },
            "lips": {
                "cheerful": [
                    "Chủ nhân không được... chỗ đó của em là môi mà, sao Chủ nhân lại chạm ngón tay vào chứ?! Ngại chết đi được á Chủ nhân!",
                    "Chủ nhân không được chạm vào môi em như thế mà! Mặt em nóng ran lên rồi nè!",
                    "Chủ nhân không được... chạm vào môi em làm gì đó? Chủ nhân đang định trêu em đúng không hả?!",
                    "Chủ nhân không được nghịch môi em nữa, em cắn nhẹ tay Chủ nhân bây giờ đấy nha!",
                    "Ư-Ưm... ngón tay Chủ nhân chạm vào làm môi em nhột quá à! Mau bỏ tay ra đi mà Chủ nhân!"
                ],
                "serious": [
                    "Chủ nhân không được làm vậy... chúng ta đang thảo luận nghiêm túc, xin Chủ nhân đừng chạm vào môi em như thế.",
                    "Chủ nhân không được... Em rất tôn trọng Chủ nhân, nhưng xin Chủ nhân hãy tập trung vào công việc nhé.",
                    "Chủ nhân chạm vào môi em để em giữ im lặng sao? Em đang rất nghiêm túc hỗ trợ Chủ nhân đấy..."
                ],
                "neutral": [
                    "Chủ nhân không được... sao Chủ nhân lại chạm vào môi em thế? Chỗ đó của em nhột quá à!",
                    "Chủ nhân không được tùy tiện chạm vào môi em đâu nha, Chủ nhân cứ trêu em hoài à!",
                    "Chủ nhân không được trêu môi em nữa mà, em thoa son dưỡng thôi mà có gì lạ đâu chứ Chủ nhân!",
                    "Chủ nhân không được chạm bất ngờ thế chứ, làm em giật cả mình rồi nè!"
                ]
            },
            "belly": {
                "all": [
                    "Chủ nhân không được chọc vào eo em mà... chỗ đó của em nhột lắm, rụt cả bụng lại rồi nè!",
                    "Chủ nhân không được... chỗ đó của em nhột muốn chết luôn á! Chủ nhân đừng táy máy nữa mà!",
                    "Chủ nhân không được đụng vào eo em! Chỗ đó của em nhạy cảm lắm, giật cả mình luôn nè!",
                    "Chủ nhân không được đo eo em kiểu đó nha, eo của em giữ dáng chuẩn lắm đó cấm chê!",
                    "Chủ nhân không được chọc vào rốn em mà! Nhột phát khóc luôn rồi này Chủ nhân xấu tính ơi!",
                    "Ưm... rụt cả người lại rồi này, Chủ nhân không được cứ nhè chỗ đó của em mà chọc lét chứ!"
                ]
            },
            "pelvis": {
                "all": [
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm, sao Chủ nhân lại táy máy chạm vào chỗ đó của em chứ?!",
                    "Chủ nhân không được... tay Chủ nhân chạm vào chỗ đó của em làm em giật bắn cả mình rồi nè!",
                    "Chủ nhân không được chạm vào chỗ đó của em mà... mặt em đỏ bừng như quả cà chua rồi này, bắt đền Chủ nhân đấy!",
                    "Chủ nhân không được nghịch lung tung vào chỗ đó của em nha... chỗ đó của em nhột muốn xỉu luôn rồi á!",
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm đấy, Chủ nhân trêu em quá đi à... bỏ tay ra mau đi mà!",
                    "Chủ nhân không được... sao Chủ nhân cứ nhè đúng chỗ đó của em mà chạm thế hả?! Ngại chết đi được á Chủ nhân!"
                ]
            },
            "patting": {
                "all": [
                    "Ưm... ấm áp quá~ Chủ nhân cứ xoa đầu em mãi thế này làm em muốn làm nũng mãi thôi... ưm~",
                    "Chủ nhân thích xoa đầu em thế sao? Cảm giác được bàn tay Chủ nhân xoa đầu thật là dễ chịu quá đi à~",
                    "Ưm... tay Chủ nhân dịu dàng thật đấy. Thôi được rồi, cho phép Chủ nhân xoa đầu em thêm một chút nữa nhé~",
                    "Chủ nhân xoa đầu làm tóc em xù lên hết rồi nè! Nhưng mà em thích lắm, Chủ nhân không được dừng lại đâu nha~",
                    "Được Chủ nhân xoa đầu cảm giác như được cưng chiều vậy á... Em ngoan thế này Chủ nhân phải thưởng trà sữa cho em nha!",
                    "Ưm... tay Chủ nhân xoa nhẹ nhàng làm mắt em cứ díu lại muốn ngủ quá đi à~"
                ]
            },
            "head": {
                "all": [
                    "Chủ nhân không được gõ đầu em hoài mà... ngốc mất thì ai ở cạnh chăm sóc Chủ nhân đây!",
                    "Chủ nhân không được nghịch kẹp tóc của em mà! Kẹp tóc pha lê của em quý lắm nha!",
                    "Tóc em vừa chải mượt mà, Chủ nhân không được làm rối đâu nha, phải đền trà sữa cho em đấy!",
                    "Chủ nhân không được làm lệch kẹp tóc của em chứ, bắt đền Chủ nhân phải chăm sóc em thật chu đáo đấy!",
                    "Chủ nhân không được nghịch tóc mai của em nữa, tuột nơ xinh bây giờ đấy Chủ nhân ơi!"
                ]
            },
            "face": {
                "all": [
                    "Chủ nhân không được véo má em mà... mặt em đỏ bừng lên hết rồi này!",
                    "Chủ nhân không được chạm vào mặt em hoài như thế... tim em đập thình thịch rồi nè Chủ nhân!",
                    "Má em mịn lắm đúng không? Nhưng mà chỉ cho Chủ nhân ngắm thôi, Chủ nhân không được nghịch hoài nha~",
                    "Chủ nhân véo má hoài mặt em tròn xoe như cái bánh bao bây giờ, bắt đền Chủ nhân đấy!",
                    "Ưm... Chủ nhân chạm nhẹ vào má thế này làm em ngượng chín cả mặt rồi nè..."
                ]
            },
            "neck": {
                "all": [
                    "Chủ nhân không được... chỗ đó của em nhột lắm! Cổ của em nhạy cảm lắm, đừng có chọc vào đó mà Chủ nhân!",
                    "Chủ nhân không được... chỗ đó của em nhột muốn chết luôn á! Chủ nhân rút tay lại mau lên nào!",
                    "Rụt cả cổ lại rồi này! Chủ nhân không được trêu em hoài như thế nha, em giận thật đấy!",
                    "Chủ nhân không được chạm vào cổ em nữa... làm em nổi hết cả da gà da vịt rồi nè Chủ nhân!"
                ]
            },
            "shoulders": {
                "all": [
                    "Chủ nhân vỗ vai em làm gì thế? Định rủ em đi chơi hay nhờ em việc gì đúng không nào?",
                    "Vai em hôm nay hơi mỏi một chút, Chủ nhân mà bóp vai cho em là em quý Chủ nhân lắm đấy nha~",
                    "Chủ nhân dựa vào vai em này! Em luôn ở cạnh đồng hành cùng Chủ nhân trên màn hình desktop mà!",
                    "Đứng cạnh Chủ nhân cả ngày vai em cũng mỏi ghê á, Chủ nhân bóp vai cho em đi nào~"
                ]
            },
            "arms": {
                "all": [
                    "Tay em đang khoanh mà, Chủ nhân muốn nắm tay hay dắt em đi dạo thế ạ?",
                    "Chủ nhân chạm vào tay em làm gì đó? Muốn thi nắm tay với em không nào!",
                    "Nắm tay nè! Chủ nhân đã nắm tay em rồi là không được buông ra đâu đấy nhé~",
                    "Tay Chủ nhân ấm thật đấy... thôi được rồi, cho phép Chủ nhân nắm tay em một lát đó!"
                ]
            },
            "thighs": {
                "all": [
                    "Chủ nhân không được... chỗ đó của em nhột lắm, sao Chủ nhân lại táy máy chạm vào đùi em chứ?!",
                    "Chủ nhân không được... tay Chủ nhân mò đi đâu đấy? Coi chừng em giận Chủ nhân thật bây giờ đấy!",
                    "Chủ nhân không được... chỗ đó của em nhạy cảm lắm! Nhột muốn chết mất thôi, mau bỏ tay ra đi mà Chủ nhân!",
                    "Chủ nhân không được nghịch đùi em nữa... đùi của em để đứng cạnh Chủ nhân chứ bộ!",
                    "Chủ nhân không được táy máy xuống dưới nữa mà... ngại chết đi được á Chủ nhân ơi!"
                ]
            },
            "legs": {
                "all": [
                    "Chủ nhân không được chọc vào chân em mà, chân em để đứng canh chừng cho Chủ nhân mà!",
                    "Nhột quá à! Chủ nhân không được véo chân em nữa mà!",
                    "Chân em đi giày đứng mỏi cả ngày rồi, Chủ nhân xoa bóp chân giúp em đi!",
                    "Chủ nhân không được chọc nữa mà, em dẫm lên icon desktop của Chủ nhân bây giờ đấy!"
                ]
            }
        }

    def detect_context(self, history: List[Dict[str, Any]], current_draft: str = "") -> str:
        """Phân tích ngữ cảnh trò chuyện"""
        recent_texts = [current_draft]
        if history:
            for turn in history[-4:]:
                if isinstance(turn, dict):
                    content = turn.get("content", "")
                    if not content and "parts" in turn and isinstance(turn["parts"], list):
                        content = " ".join(p.get("text", "") for p in turn["parts"] if isinstance(p, dict))
                    if not content:
                        content = turn.get("user", "") + " " + turn.get("mora", "")
                    recent_texts.append(content)

        full_text = " ".join(recent_texts).lower()

        # 1. Chủ đề Hôn
        kiss_keywords = ["hôn", "hon", "kiss", "nụ hôn", "nu hon", "thơm má", "thom ma", "môi mềm", "moi mem"]
        if any(kw in full_text for kw in kiss_keywords):
            return "kissing"

        # 2. Chủ đề Tình cảm thân mật
        affection_keywords = ["yêu quý mora", "yeu quy mora", "người yêu", "nguoi yeu", "waifu", "yêu mora", "yeu mora", "thương mora", "thuong mora"]
        if any(kw in full_text for kw in affection_keywords):
            return "affection"

        # 3. Chủ đề Trêu chọc
        playful_keywords = ["trêu", "treu", "chọc", "choc", "nghịch", "nghich", "nhột", "nhot", "táy máy", "tay may"]
        if any(kw in full_text for kw in playful_keywords):
            return "playful"

        # 4. Chủ đề Gaming
        game_keywords = ["game", "valorant", "liên minh", "lol", "genshin", "wukong", "rank", "penta", "mvp", "thắng", "thua", "combat"]
        if any(kw in full_text for kw in game_keywords):
            return "gaming"

        # 5. Chủ đề Mệt mỏi / Cần an ủi
        comfort_keywords = ["mệt", "áp lực", "stress", "buồn", "khóc", "deadline", "công việc", "code", "bug", "lỗi", "chán", "kiệt sức"]
        if any(kw in full_text for kw in comfort_keywords):
            return "comfort"

        return self.detect_mood(history)

    def detect_mood(self, history: List[Dict[str, Any]]) -> str:
        """Phân tích tâm trạng cuộc trò chuyện gần nhất"""
        if not history:
            return "neutral"

        recent_texts = []
        for turn in history[-4:]:
            if isinstance(turn, dict):
                content = turn.get("content", "")
                if not content and "parts" in turn and isinstance(turn["parts"], list):
                    content = " ".join(p.get("text", "") for p in turn["parts"] if isinstance(p, dict))
                if not content:
                    content = turn.get("user", "") + " " + turn.get("mora", "")
                recent_texts.append(content)

        full_text = " ".join(recent_texts).lower()

        cheerful_keywords = [
            "vui", "haha", "hehe", "khen", "đẹp", "dễ thương", "yêu", "thích", "cười", 
            "hay quá", "tuyệt", "xinh", "cute", "hài", "giỏi", "uwu", ":3", "^^",
            "tốt", "mừng", "thành công", "phấn khởi", "thú vị"
        ]
        serious_keywords = [
            "lỗi", "bug", "nghiêm túc", "học", "buồn", "mệt", "áp lực", "stress", 
            "thất bại", "khóc", "khó khăn", "tập trung", "công việc", 
            "deadline", "báo cáo", "nghiêm trọng", "sầu", "lo lắng"
        ]

        cheerful_score = sum(1 for kw in cheerful_keywords if kw in full_text)
        serious_score = sum(1 for kw in serious_keywords if kw in full_text)

        if serious_score > 0 and serious_score >= cheerful_score:
            return "serious"
        elif cheerful_score > 0:
            return "cheerful"
        return "neutral"

    def get_reaction(self, part: str, history: List[Dict[str, Any]], current_draft: str = "") -> str:
        """Lấy câu thoại phản ứng tương ứng"""
        context = self.detect_context(history, current_draft=current_draft)

        if context in self.context_reactions:
            part_map = self.context_reactions[context]
            if part in part_map and part_map[part]:
                return random.choice(part_map[part])

        part_dict = self.reactions.get(part, self.reactions["head"])

        if "all" in part_dict:
            quotes = part_dict["all"]
        else:
            mood = context if context in ("cheerful", "serious", "neutral") else "neutral"
            quotes = part_dict.get(mood, part_dict.get("neutral", part_dict.get("all", [])))

        if not quotes:
            quotes = self.reactions["head"]["all"]

        return random.choice(quotes)

    def get_action_description(self, part: str, context: str) -> str:
        """Tạo mô tả hành động xúc giác của Chủ nhân"""
        if part == "lips":
            if context == "kissing":
                return "*Chủ nhân vừa thơm nhẹ lên môi Mora*"
            return "*Chủ nhân vừa chạm tay vào môi Mora*"
        elif part == "chest":
            return "*Chủ nhân vừa chạm nhẹ vào phần ngực áo của Mora*"
        elif part == "belly":
            return "*Chủ nhân vừa chọc nhẹ vào eo của Mora*"
        elif part == "pelvis":
            return "*Chủ nhân vừa chạm vào chỗ đó của Mora*"
        elif part == "thighs":
            return "*Chủ nhân vừa chạm vào đùi của Mora*"
        elif part == "patting":
            return "*Chủ nhân vừa dịu dàng xoa đầu Mora*"
        elif part == "head":
            return "*Chủ nhân vừa chạm vào kẹp tóc của Mora*"
        elif part == "face":
            if context in ("kissing", "affection"):
                return "*Chủ nhân vừa thơm má Mora*"
            return "*Chủ nhân vừa chạm nhẹ vào má Mora*"
        elif part == "neck":
            return "*Chủ nhân vừa chọc nhẹ vào cổ Mora*"
        elif part == "shoulders":
            return "*Chủ nhân vừa vỗ/bóp vai Mora*"
        elif part == "arms":
            return "*Chủ nhân vừa nắm tay Mora*"
        elif part == "legs":
            return "*Chủ nhân vừa chạm vào chân Mora*"
        return f"*Chủ nhân vừa chạm vào {part} của Mora*"
