# blockchain.py
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

# URL del nodo RPC de zkSYS Testnet
# Obtén la URL actualizada en: https://docs.syscoin.org
ZKSYS_TESTNET_RPC = "https://rpc.zkSYS.testnet.syscoin.org"  

def conectar():
    """Conecta con zkSYS Testnet."""
    try:
        w3 = Web3(Web3.HTTPProvider(ZKSYS_TESTNET_RPC))
        if w3.is_connected():
            print(f"✅ Conectado a zkSYS Testnet. Bloque actual: {w3.eth.block_number}")
            return w3
        else:
            print("⚠️ No se pudo conectar a zkSYS. Modo simulación activado.")
            return None
    except Exception as e:
        print(f"⚠️ Error de conexión: {e}. Modo simulación activado.")
        return None

def registrar_evento_en_blockchain(dog_id, user_id, tipo_evento, descripcion):
    """
    Registra un evento en la blockchain como transacción con datos.
    En testnet esto no cuesta dinero real.
    Devuelve el hash de la transacción o None si falla.
    """
    w3 = conectar()
    
    if not w3:
        # Modo simulación: genera un hash falso para desarrollo
        import hashlib, time
        hash_simulado = "0x" + hashlib.sha256(
            f"{dog_id}{user_id}{tipo_evento}{time.time()}".encode()
        ).hexdigest()
        print(f"[SIMULACIÓN BLOCKCHAIN] Hash: {hash_simulado}")
        return hash_simulado
    
    try:
        wallet_publica = os.getenv("WALLET_PUBLICA")
        wallet_privada = os.getenv("WALLET_PRIVADA")
        
        if not wallet_publica or wallet_publica == "aqui_va_tu_direccion_publica_0x...":
            return None
        
        # Datos del evento (codificados en hex)
        datos_evento = f"RESCUEPAW|{dog_id}|{user_id}|{tipo_evento}|{descripcion}"
        datos_hex = datos_evento.encode().hex()
        
        # Construir transacción
        nonce = w3.eth.get_transaction_count(wallet_publica)
        tx = {
            "nonce": nonce,
            "to": wallet_publica,  # Se envía a sí mismo (solo para registrar datos)
            "value": 0,
            "gas": 21000 + len(datos_hex),
            "gasPrice": w3.eth.gas_price,
            "data": "0x" + datos_hex,
            "chainId": w3.eth.chain_id
        }
        
        # Firmar y enviar
        tx_firmada = w3.eth.account.sign_transaction(tx, wallet_privada)
        tx_hash = w3.eth.send_raw_transaction(tx_firmada.rawTransaction)
        return tx_hash.hex()
        
    except Exception as e:
        print(f"[ERROR blockchain] {e}")
        return None

def obtener_saldo_testnet(direccion_wallet):
    """Obtiene el saldo de SYS en testnet de una wallet."""
    w3 = conectar()
    if not w3:
        return 10.0  # Simulación
    try:
        saldo_wei = w3.eth.get_balance(direccion_wallet)
        return w3.from_wei(saldo_wei, "ether")
    except:
        return 0.0