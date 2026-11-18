import unittest
from sistemas import PERFIS, migrar_estado, gerar_caso, novo_estado_investigacao, avaliar_hipotese

class SistemasTests(unittest.TestCase):
    def test_migracao_preserva_campos_legados(self):
        antigo={"jogador":"Douglas","status":"jogando","sala":2,"inventario":["Chave"],
                "vistos":["hall:retrato"],"tempo_restante":333,"conquistas":["x"]}
        novo=migrar_estado(antigo)
        self.assertEqual(novo["jogador"],"Douglas")
        self.assertEqual(novo["sala"],2)
        self.assertEqual(novo["inventario"],["Chave"])
        self.assertEqual(novo["tempo_restante"],333)
        self.assertEqual(novo["dificuldade"],"investigador")
        self.assertEqual(novo["schema_version"],2)

    def test_caso_reproduzivel(self):
        self.assertEqual(gerar_caso(1234),gerar_caso(1234))
        self.assertIn("culpado", gerar_caso(5678))

    def test_perfis(self):
        self.assertEqual(set(PERFIS),{"historia","investigador","pesadelo"})
        self.assertGreater(PERFIS["historia"]["tentativas"],PERFIS["pesadelo"]["tentativas"])

    def test_hipotese_exige_evidencias(self):
        estado={"campanha":{"caso":gerar_caso(1234)},"investigacao":novo_estado_investigacao()}
        resultado=avaliar_hipotese(estado,estado["campanha"]["caso"]["culpado"])
        self.assertFalse(resultado["fundamentada"])

if __name__=="__main__":
    unittest.main()
