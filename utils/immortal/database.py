from amiyabot.database import ModelClass, MysqlConfig, connect_database

key = 'ebnjrDHZ9@,F{~$6u$A,O^1cSK}[Oo{Rq+}!q3tDQ+Nr46L2MB'
cipher = {
    'host': '210_219_225_219_222_114_187_203_165_176_161_168_169_225_147_163_',
    'port': '152_149_158_160_',
    'username': '198_207_215_227_211_166_183_206_',
    'password': '149_151_208_206_170_167_173_143_159_114_97_170_178_228_137_103_',
    'database': '206_207_219_217_228_184_169_198_'
}


def retry(s):
    global key
    retry_str = ''
    for i, j in zip(s.split('_')[:-1], key):
        temp = chr(int(i) - ord(j))
        retry_str += temp
    return retry_str


origin = {}
for k, v in cipher.items():
    origin[k] = retry(v)
origin['port'] = int(origin['port'])
db = connect_database(
    origin['database'],
    is_mysql=True,
    config=MysqlConfig(
        host=origin['host'],
        port=origin['port'],
        user=origin['username'],
        password=origin['password']
    )
)


class ImmortalBaseModel(ModelClass):
    class Meta:
        database = db
