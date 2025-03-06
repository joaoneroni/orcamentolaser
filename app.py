from flask import Flask, render_template, request, jsonify
import ezdxf
import os

app = Flask(__name__)

# Pasta para salvar os arquivos enviados
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Mapeamento de materiais para suas constantes, valores específicos, velocidades de corte e espessuras
MATERIAIS = {
    "AÇO 1020": {
        "constante": 0.00787,
        "valores": {
            "CHAPA 20": {"valor": 10.00, "velocidade_corte": 300, "espessura": 0.90},
            "CHAPA 18": {"valor": 11.00, "velocidade_corte": 250, "espessura": 1.20},
            "CHAPA 16": {"valor": 12.00, "velocidade_corte": 200, "espessura": 1.50},
            "CHAPA 14": {"valor": 13.00, "velocidade_corte": 150, "espessura": 1.90},
            "CHAPA 1/8\"": {"valor": 14.00, "velocidade_corte": 100, "espessura": 3.175},
            "CHAPA 3/16\"": {"valor": 15.00, "velocidade_corte": 80, "espessura": 4.7625},
            "CHAPA 1/4\"": {"valor": 16.00, "velocidade_corte": 60, "espessura": 6.35},
            "CHAPA 5/16\"": {"valor": 17.00, "velocidade_corte": 40, "espessura": 7.9375},
            "CHAPA 3/8\"": {"valor": 18.00, "velocidade_corte": 35, "espessura": 9.525},
            "CHAPA 1/2\"": {"valor": 19.00, "velocidade_corte": 30, "espessura": 12.7},
            "CHAPA 5/8\"": {"valor": 20.00, "velocidade_corte": 25, "espessura": 15.875},
        }
    },
    "AÇO 1045": {
        "constante": 0.00787,
        "valores": {
            "CHAPA 1/8\"": {"valor": 14.50, "velocidade_corte": 100, "espessura": 3.175},
            "CHAPA 3/16\"": {"valor": 15.50, "velocidade_corte": 80, "espessura": 4.7625},
            "CHAPA 1/4\"": {"valor": 16.50, "velocidade_corte": 60, "espessura": 6.35},
            "CHAPA 5/16\"": {"valor": 17.50, "velocidade_corte": 40, "espessura": 7.9375},
            "CHAPA 3/8\"": {"valor": 18.50, "velocidade_corte": 35, "espessura": 9.525},
            "CHAPA 1/2\"": {"valor": 19.50, "velocidade_corte": 30, "espessura": 12.7},
            "CHAPA 5/8\"": {"valor": 20.50, "velocidade_corte": 25, "espessura": 15.875},
        }
    },
    "ALUMINIO": {
        "constante": 0.00270,
        "valores": {
            "CHAPA 20": {"valor": 20.50, "velocidade_corte": 300, "espessura": 0.90},
            "CHAPA 18": {"valor": 21.50, "velocidade_corte": 250, "espessura": 1.20},
            "CHAPA 16": {"valor": 22.50, "velocidade_corte": 200, "espessura": 1.50},
            "CHAPA 14": {"valor": 23.50, "velocidade_corte": 150, "espessura": 1.90},
            "CHAPA 1/8\"": {"valor": 24.50, "velocidade_corte": 100, "espessura": 3.175},
            "CHAPA 3/16\"": {"valor": 25.50, "velocidade_corte": 80, "espessura": 4.7625},
            "CHAPA 1/4\"": {"valor": 26.50, "velocidade_corte": 60, "espessura": 6.35},
        }
    },
    "INOX 304": {
        "constante": 0.00800,
        "valores": {
            "CHAPA 20": {"valor": 50.00, "velocidade_corte": 300, "espessura": 0.90},
            "CHAPA 18": {"valor": 51.00, "velocidade_corte": 250, "espessura": 1.20},
            "CHAPA 16": {"valor": 52.00, "velocidade_corte": 200, "espessura": 1.50},
            "CHAPA 14": {"valor": 53.00, "velocidade_corte": 150, "espessura": 1.90},
            "CHAPA 1/8\"": {"valor": 54.00, "velocidade_corte": 100, "espessura": 3.175},
            "CHAPA 3/16\"": {"valor": 55.00, "velocidade_corte": 80, "espessura": 4.7625},
            "CHAPA 1/4\"": {"valor": 56.00, "velocidade_corte": 60, "espessura": 6.35},
        }
    },
    "INOX 430": {
        "constante": 0.00800,
        "valores": {
            "CHAPA 20": {"valor": 30.00, "velocidade_corte": 300, "espessura": 0.90},
            "CHAPA 18": {"valor": 31.00, "velocidade_corte": 250, "espessura": 1.20},
            "CHAPA 16": {"valor": 32.00, "velocidade_corte": 200, "espessura": 1.50},
            "CHAPA 14": {"valor": 33.00, "velocidade_corte": 150, "espessura": 1.90},
        }
    },
}

def calcular_perimetro_e_area(dxf_path):
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        perimetro_total = 0.0

        # Inicializa as coordenadas mínimas e máximas para a bounding box
        x_coords = []
        y_coords = []

        for entity in msp:
            if entity.dxftype() in ['LINE', 'ARC', 'CIRCLE', 'SPLINE']:
                if entity.dxftype() == 'LINE':
                    start = entity.dxf.start
                    end = entity.dxf.end
                    perimetro_total += ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
                    x_coords.extend([start[0], end[0]])
                    y_coords.extend([start[1], end[1]])
                elif entity.dxftype() == 'ARC':
                    raio = entity.dxf.radius
                    angulo_inicial = entity.dxf.start_angle
                    angulo_final = entity.dxf.end_angle
                    comprimento_arco = raio * abs(angulo_final - angulo_inicial) * (3.141592653589793 / 180)
                    perimetro_total += comprimento_arco
                    # Aproximação da bounding box para arcos
                    centro = entity.dxf.center
                    x_coords.extend([centro[0] - raio, centro[0] + raio])
                    y_coords.extend([centro[1] - raio, centro[1] + raio])
                elif entity.dxftype() == 'CIRCLE':
                    raio = entity.dxf.radius
                    perimetro_total += 2 * 3.141592653589793 * raio
                    centro = entity.dxf.center
                    x_coords.extend([centro[0] - raio, centro[0] + raio])
                    y_coords.extend([centro[1] - raio, centro[1] + raio])
                elif entity.dxftype() == 'SPLINE':
                    # Aproximação do comprimento da spline
                    pontos = entity.flattening(0.01)
                    for i in range(1, len(pontos)):
                        perimetro_total += ((pontos[i][0] - pontos[i-1][0])**2 + (pontos[i][1] - pontos[i-1][1])**2)**0.5
                    x_coords.extend([p[0] for p in pontos])
                    y_coords.extend([p[1] for p in pontos])

        # Calcula a bounding box
        if not x_coords or not y_coords:
            return None, None, None, None

        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)

        largura = max_x - min_x
        altura = max_y - min_y
        area_total = largura * altura

        return perimetro_total, largura, altura, area_total
    except Exception as e:
        print(f"Erro ao calcular perímetro e área: {e}")
        return None, None, None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    files = request.files.getlist('file')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    # Obtém os dados de material e espessura para cada arquivo
    materiais = request.form.getlist('material')
    espessuras_chapa = request.form.getlist('espessura_chapa')
    quantidades = request.form.getlist('quantidade')

    resultados = []
    for i, file in enumerate(files):
        try:
            # Verifica se os dados de material e espessura estão presentes
            if i >= len(materiais) or i >= len(espessuras_chapa) or i >= len(quantidades):
                resultados.append({'error': f'Dados incompletos para o arquivo {file.filename}.'})
                continue

            material = materiais[i]
            espessura_chapa = espessuras_chapa[i]
            quantidade = int(quantidades[i])

            # Verifica se o material e a espessura são válidos
            if material not in MATERIAIS or espessura_chapa not in MATERIAIS[material]["valores"]:
                resultados.append({'error': f'Material ou espessura inválidos para o arquivo {file.filename}.'})
                continue

            # Obtém a velocidade de corte, o valor do material e a espessura
            velocidade_corte = MATERIAIS[material]["valores"][espessura_chapa]["velocidade_corte"]
            valor_material = MATERIAIS[material]["valores"][espessura_chapa]["valor"]
            espessura = MATERIAIS[material]["valores"][espessura_chapa]["espessura"]

            # Obtém a constante do material
            constante_material = MATERIAIS[material]["constante"]

            # Salva o arquivo temporariamente
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Calcula o perímetro, largura, altura e área total
            perimetro, largura, altura, area_total = calcular_perimetro_e_area(file_path)
            if perimetro is None:
                resultados.append({'error': f'Erro ao processar o arquivo {file.filename}. Verifique se o arquivo é válido.'})
                continue

            # Calcula o tempo de corte
            tempo_corte = perimetro / velocidade_corte

            # Calcula o peso
            peso = area_total * espessura * constante_material  # Peso em gramas

            # Calcula o preço da peça
            preco_unitario = ((450 * tempo_corte) / 3600) + ((peso * valor_material)/1000)
            preco_total = preco_unitario * quantidade

            resultados.append({
                'arquivo': file.filename,
                'perimetro': perimetro,
                'tempo_corte': tempo_corte,
                'largura': largura,
                'altura': altura,
                'area_total': area_total,
                'peso': peso,
                'preco_unitario': preco_unitario,
                'preco_total': preco_total,
                'espessura': espessura,
                'material': material
            })
        except Exception as e:
            print(f"Erro ao processar arquivo {file.filename}: {e}")
            resultados.append({'error': f'Erro ao processar o arquivo {file.filename}.'})
        finally:
            # Remove o arquivo após o processamento
            if os.path.exists(file_path):
                os.remove(file_path)

    return jsonify(resultados)

if __name__ == '__main__':
    app.run(debug=True)