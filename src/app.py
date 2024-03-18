from flask import Flask,request,jsonify
from flask_pymongo import PyMongo,ObjectId
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime
import pytz



app = Flask(__name__)
app.config['MONGO_URI']='mongodb://localhost/pythonreactdb'
mongo=PyMongo(app)
db=mongo.db.users
auth_db = mongo.db.auth
tarjeta_db=mongo.db.tarjeta
compras_db = mongo.db.compras
compras_anomalas_db= mongo.db.compras_Anomalas
servicios_db= mongo.db.servicios


#para evitar el cors de node
bcrypt = Bcrypt(app) 
#para evitar el cors de node 
CORS(app)
# ruta
@app.route('/users', methods=['POST'])
def createUser():
    try:
        # Utiliza insert_one para insertar un solo documento
        result = db.insert_one({
            'name': request.json['name'],
            'email': request.json['email'],
            'password': request.json['password'],
        })
        # Obtén el ID del documento insertado
        return jsonify(str(result.inserted_id))
        #return 'received'
    except KeyError as e:
        return jsonify({'error': f'Missing key: {str(e)}'}), 400  
# Función para listar usuarios
@app.route('/users', methods=['GET'])
def getUsers():
    users = []
    for doc in db.find():
        user_data = {
            '_id': str(ObjectId(doc['_id'])),
            'name': doc.get('name', ''),
            'email': doc.get('email', ''),
            'password': doc.get('password', '')
        }
        users.append(user_data)
    return jsonify(users)
# Función para obtener un usuario por ID
@app.route('/user/<id>', methods=['GET'])
def getUser(id):
    user = db.find_one({'_id': ObjectId(id)})
    if user:
        return jsonify({
            '_id': str(ObjectId(user['_id'])),
            'name': user['name'],
            'email': user['email'],
            'password': user['password']
        })
    else:
        return jsonify({'error': 'User not found'}), 404
# Ruta para eliminar un usuario por ID
@app.route('/users/<id>', methods=['DELETE'])
def deleteUser(id):
    result = db.delete_one({'_id': ObjectId(id)})
    if result.deleted_count > 0:
        return jsonify({'message': 'User deleted successfully'})
    else:
        return jsonify({'error': 'User not found'}), 404
# Ruta para actualizar un usuario por ID
@app.route('/users/<id>', methods=['PUT'])
def updateUser(id):
    # Verifica si el usuario existe
    existing_user = db.find_one({'_id': ObjectId(id)})
    if existing_user:
        # Actualiza los campos con los nuevos valores proporcionados
        existing_user['name'] = request.json.get('name', existing_user['name'])
        existing_user['email'] = request.json.get('email', existing_user['email'])
        existing_user['password'] = request.json.get('password', existing_user['password'])

        # Guarda la actualización en la base de datos
        db.update_one({'_id': ObjectId(id)}, {'$set': existing_user})

        return jsonify({'message': 'User updated successfully'})
    else:
        return jsonify({'error': 'User not found'}), 404

#NUEVAS RUTAS
# Ruta para el registro de usuario
@app.route('/register', methods=['POST'])
def register():
    try:
        print(f"Request JSON: {request.json}")  # Imprimir el contenido de la solicitud JSON
        # Verifica si el usuario ya existe por correo electrónico
        existing_user = db.find_one({'email': request.json['email']})
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400

        # Crea un nuevo usuario en la colección "users"
        user_result = db.insert_one({
            'name': request.json['name'],
            'email': request.json['email'],
            # Otros campos de información general
        })

        # Hashea la contraseña y crea un registro en la colección "auth"
        hashed_password = bcrypt.generate_password_hash(request.json['password']).decode('utf-8')
        auth_result = auth_db.insert_one({
            'user_id': user_result.inserted_id,
            'password': hashed_password,
            # Otros campos relacionados con la autenticación
        })

        return jsonify({'message': 'User registered successfully', 'user_id': str(user_result.inserted_id)})
    except KeyError as e:
        print(f'Missing key: {str(e)}')
        return jsonify({'error': f'Missing key: {str(e)}'}), 400
    except Exception as e:
        print(f'Error during registration: {str(e)}')
        return jsonify({'error': 'Error during registration'}), 400

# Ruta para el inicio de sesiónsss
@app.route('/login', methods=['POST'])
def login():
    try:
        # Busca el usuario por su correo electrónico en la colección "users"
        user = db.find_one({'email': request.json['email']})
        if user:
            # Busca la información de autenticación en la colección "auth"
            auth_info = auth_db.find_one({'user_id': user['_id']})
            if auth_info and bcrypt.check_password_hash(auth_info['password'], request.json['password']):
                return jsonify({'message': 'Login successful', 'user_id': str(user['_id'])})
            else:
                return jsonify({'error': 'Invalid credentials'}), 401
        else:
            return jsonify({'error': 'User not found'}), 404
    except KeyError as e:
        return jsonify({'error': f'Missing key: {str(e)}'}), 400

#la parte de las tarjetas
# Ruta para agregar una nueva tarjeta
@app.route('/banco/agregar-tarjeta', methods=['POST'])
def agregar_tarjeta():
    try:
        # Inserta una nueva tarjeta en la colección 'tarjeta_db'
        tarjeta_result = tarjeta_db.insert_one({
            'nombre_propietario': request.json['nombre_propietario'],
            'numero_tarjeta': request.json['numero_tarjeta'],
            'fecha_expiracion': request.json['fecha_expiracion'],
            'cvv': request.json['cvv'],
            'saldo': request.json['saldo']
        })

        return jsonify({'message': 'Tarjeta agregada correctamente', 'tarjeta_id': str(tarjeta_result.inserted_id)})
    except KeyError as e:
        return jsonify({'error': f'Missing key: {str(e)}'}), 400

# Ruta para consultar una tarjeta por número de tarjeta
@app.route('/banco/consultar-tarjeta/<numero_tarjeta>', methods=['GET'])
def consultar_tarjeta(numero_tarjeta):
    tarjeta = tarjeta_db.find_one({'numero_tarjeta': numero_tarjeta})
    if tarjeta:
        return jsonify({
            'nombre_propietario': tarjeta['nombre_propietario'],
            'numero_tarjeta': tarjeta['numero_tarjeta'],
            'fecha_expiracion': tarjeta['fecha_expiracion'],
            'cvv': tarjeta['cvv'],
            'saldo': tarjeta['saldo']
        })
    else:
        return jsonify({'error': 'Tarjeta no encontrada'}), 404
    
#PAGOS
# Ruta para crear una compra
# @app.route('/compras', methods=['POST'])
# def createCompra():
#     try:
#         # Obtener los datos de la solicitud
#         data = request.json

#         # Obtener la fecha y hora actual
#         fecha_hora_pago = datetime.datetime.utcnow()

#         # Obtener la dirección IP del cliente
#         direccion_ip = request.remote_addr

#         # Guardar la compra en la colección "compras" junto con la fecha, hora y dirección IP
#         compras_db = mongo.db.compras
#         result = compras_db.insert_one({
#             'tarjeta': data.get('tarjeta', ''),
#             'productos': data.get('productos', []),
#             'total': data.get('total', 0),
#             'fecha_hora_pago': fecha_hora_pago,
#             'direccion_ip': direccion_ip,
#             # Puedes agregar otros campos necesarios
#         })

#         # Respondemos con el ID de la compra creada
#         return jsonify({'message': 'Compra realizada con éxito', 'compra_id': str(result.inserted_id)})

#     except Exception as e:
#         # Manejar errores
#         return jsonify({'error': str(e)}), 500

@app.route('/compras', methods=['POST'])
def createCompra():
    try:
        data = request.json
        zona_horaria_local = pytz.timezone('America/Guayaquil')  # Reemplaza con tu zona horaria local
        fecha_hora_pago = datetime.now(zona_horaria_local)
        direccion_ip = '138.199.50.102'
       # direccion_ip = request.remote_addr
        compras_anomalas_db = mongo.db.compras_Anomalas
        result = compras_anomalas_db.insert_one({
            'tarjeta': data.get('tarjeta', ''),
            'productos': data.get('productos', []),
            'total': data.get('total', 0),
            'fecha_hora_pago': fecha_hora_pago.strftime("%Y-%m-%d %H:%M:%S %p"),
            'direccion_ip': direccion_ip,
            'lugar': data.get('lugar', ''),
        })
        return jsonify({'message': 'Compra realizada con éxito', 'compra_id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
###########################mirara###########
# @app.route('/compras', methods=['POST'])
# def createCompra():
#     try:
#         # Obtener los datos de la solicitud
#         data = request.json

#         # Guardar la compra en la colección "compras"
#         compras_db = mongo.db.compras
#         result = compras_db.insert_one({
#             'tarjeta': data.get('tarjeta', ''),  # Asegúrate de obtener 'tarjeta' del objeto 'data'
#             'productos': data.get('productos', []),  # Asegúrate de obtener 'productos' del objeto 'data'
#             'total': data.get('total', 0),  # Asegúrate de obtener 'total' del objeto 'data'
#             # Puedes agregar otros campos necesarios
#         })

#         # Respondemos con el ID de la compra creada
#         return jsonify({'message': 'Compra realizada con éxito', 'compra_id': str(result.inserted_id)})
#         #return jsonify({'message': 'Compra realizada con éxito', 'compra_id': str(result.inserted_id)})

#     except Exception as e:
#         # Manejar errores
#         return jsonify({'error': str(e)}), 500
# @app.route('/compras', methods=['POST'])
# def createCompra():
#     try:
#         # Obtener los datos de la solicitud
#         data = request.json

#         # Guardar la compra en la colección "compras"
#         compras_db = mongo.db.compras
#         result = compras_db.insert_one({
#             'tarjeta': data['tarjeta'],
#             'productos': data['productos'],
#             'total': data['total'],
#             # Puedes agregar otros campos necesarios
#         })

#         # Respondemos con el ID de la compra creada
#         return jsonify({'message': 'Compra realizada con éxito', 'compra_id': str(result.inserted_id)})

#     except Exception as e:
#         # Manejar errores
#         return jsonify({'error': str(e)}), 500
#servicios
# Ruta para procesar el pago de servicios
# Ruta para procesar el pago de servicios
@app.route('/servicios/pagar', methods=['POST'])
def procesar_pago_servicio():
    try:
        # Obtener los datos del pago desde la solicitud
        data = request.json

        # Guardar los detalles del pago en la colección "servicios"
        servicios_db = mongo.db.servicios
        result = servicios_db.insert_one({
            'servicio': data['servicio'],
            'monto': data['monto'],
            'codigo_pago': data['codigoPago'],  # Guardar el código de pago
            'nombre': data['nombre'],
            'cedula': data['cedula'],
            'fecha_pago': data['fechaPago'],
            'ip_pago': data['ipPago'],
            
        })

        # Responder con un mensaje de éxito
        return jsonify({'message': 'Pago procesado correctamente', 'pago_id': str(result.inserted_id)})
    except Exception as e:
        # Manejar errores
        return jsonify({'error': str(e)}), 500

    
if __name__ == "__main__":
    app.run(debug=True)