import krpc

conn = krpc.connect(name='Teste de Conexão')
print(f'Conctado ao KSP: {conn.krpc.get_status().version}')
