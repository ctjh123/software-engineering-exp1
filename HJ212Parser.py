# -*- coding: utf-8 -*-
"""
HJ212Parser.py
==============
HJ 212-2017《污染物在线监控（监测）系统数据传输标准》报文解析类库。

报文结构（通信包）：
    ##  +  4位数据段长度  +  数据段  +  4位CRC(HEX)  +  \\r\\n
    包头     (十进制,如0101)   QN=...;...;CP=&&..&&   高字节在前

数据段顶层字段：
    QN  请求编号(时间戳)   ST  系统编码   CN  命令编号
    PW  访问密码           MN  设备唯一标识  Flag 标志位
    CP  &&数据内容&&

作者：202410760241 朱邦煦
"""

import re


class HJ212Parser:
    """HJ 212-2017 协议报文解析器。

    典型用法：
        p = HJ212Parser()
        p.is_valid_message(msg)        # 格式校验
        p.validate_crc(msg)            # CRC16 校验
        p.parse_data_segment(msg)     # 数据段 -> dict
        p.extract_monitoring_data(msg) # 监测因子 -> {编码: 实时值}
    """

    # 通信包整体结构：## + 4位长度 + 数据段(非贪婪) + 4位HEX-CRC + 可选\r\n
    _PKT_RE = re.compile(r'^##(\d{4})(.+?)([0-9A-Fa-f]{4})\r?\n?$')

    # CP 段：CP=&& ... && （必须出现在数据段末尾）
    _CP_RE = re.compile(r'^(.+?;)?CP=&&(.*)&&$')

    # 监测因子实时值：形如 a11001-Rtd=0.050
    _MONITOR_RE = re.compile(r'^([A-Za-z]\w*)-Rtd=(-?\d+(?:\.\d+)?)')

    # ------------------------------------------------------------------ #
    # ANSI CRC16 （HJ 212-2017 附录 A）
    #   初始值 0xFFFF，多项式 0xA001，高字节在前
    # ------------------------------------------------------------------ #
    @staticmethod
    def _crc16(data: bytes) -> int:
        # 严格按 HJ 212-2017 附录 A 的 C 代码实现：crc=(crc>>8)^byte
        crc = 0xFFFF
        for byte in data:
            crc = (crc >> 8) ^ byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF

    # ------------------------------------------------------------------ #
    # 1) 报文格式合法性
    # ------------------------------------------------------------------ #
    def is_valid_message(self, message: str) -> bool:
        """检查报文格式是否正确（帧头/4位长度/4位CRC/帧尾）。"""
        if not isinstance(message, str) or not message:
            return False
        m = self._PKT_RE.match(message)
        if not m:
            return False
        # 长度字段必须与真实数据段长度一致
        declared_len = int(m.group(1))
        actual_len = len(m.group(2).encode('ascii', errors='ignore'))
        return declared_len == actual_len

    # ------------------------------------------------------------------ #
    # 2) CRC16 校验
    # ------------------------------------------------------------------ #
    def validate_crc(self, message: str) -> bool:
        """校验报文中附带的 CRC 是否等于对数据段重算的结果。"""
        m = self._PKT_RE.match(message) if isinstance(message, str) else None
        if not m:
            return False
        data_segment = m.group(2)            # 仅数据段参与 CRC
        received = m.group(3).upper()
        calc = self._crc16(data_segment.encode('ascii'))
        return f'{calc:04X}' == received

    # ------------------------------------------------------------------ #
    # 3) 数据段结构化解析
    # ------------------------------------------------------------------ #
    def parse_data_segment(self, message: str) -> dict:
        """解析数据段，返回顶层键值对字典。

        例如返回：
            {'QN': '20160801085857223', 'ST': '32', 'CN': '1062',
             'PW': '100000', 'MN': '010000A8900016F000169DC0',
             'Flag': '5', 'CP': 'RtdInterval=30'}
        """
        m = self._PKT_RE.match(message) if isinstance(message, str) else None
        if not m:
            raise ValueError('报文格式不合法，无法解析数据段')

        data_segment = m.group(2)
        result = {}

        cp_match = self._CP_RE.match(data_segment)
        if cp_match:
            result['CP'] = cp_match.group(2)            # && 之间的内容
            head = cp_match.group(1) or ''              # CP 之前的部分
        else:
            head = data_segment

        head = head.rstrip(';')
        for pair in head.split(';'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                result[k] = v
        return result

    # ------------------------------------------------------------------ #
    # 4) 监测因子提取
    # ------------------------------------------------------------------ #
    def extract_monitoring_data(self, message: str) -> dict:
        """从 CP 字段中提取所有监测因子及其实时值(Rtd)。

        返回：{因子编码: float 实时值}，例如 {'a11001': 0.05, 'a01001': 25.6}
        """
        seg = self.parse_data_segment(message)
        cp = seg.get('CP', '')
        monitors = {}
        for item in cp.split(';'):
            m = self._MONITOR_RE.match(item.strip())
            if m:
                monitors[m.group(1)] = float(m.group(2))
        return monitors


# ---------------------------------------------------------------------- #
# 自测：直接运行本文件即可看到官方黄金向量校验结果
# ---------------------------------------------------------------------- #
if __name__ == '__main__':
    # HJ 212-2017 附录 A 官方示例报文，CRC 应为 1C80
    official = (
        '##0101QN=20160801085857223;ST=32;CN=1062;PW=100000;'
        'MN=010000A8900016F000169DC0;Flag=5;CP=&&RtdInterval=30&&1C80\r\n'
    )
    p = HJ212Parser()
    print('格式合法 :', p.is_valid_message(official))
    print('CRC通过  :', p.validate_crc(official))
    print('数据段   :', p.parse_data_segment(official))

    # 一条实时数据上传报文（CN=2011），演示监测因子提取
    realtime = (
        '##0139QN=20261001100000001;ST=32;CN=2011;PW=123456;'
        'MN=ABC123456;Flag=4;CP=&&DataTime=20261001100000;'
        'a11001-Rtd=0.050,a11001-Flag=N;'
        'a01001-Rtd=25.6,a01001-Flag=N&&'
    )
    # 自动补齐 CRC 与长度
    body = realtime[2:]                          # 去掉 ##
    seg_end = body.rindex('&&') + 2              # 数据段结束(最后一个&&)
    data_seg = body[:seg_end]
    crc = p._crc16(data_seg.encode('ascii'))
    realtime = f'##{len(data_seg):04d}{data_seg}{crc:04X}\r\n'

    print('\n--- 实时数据报文 ---')
    print('格式合法 :', p.is_valid_message(realtime))
    print('CRC通过  :', p.validate_crc(realtime))
    print('监测因子 :', p.extract_monitoring_data(realtime))
