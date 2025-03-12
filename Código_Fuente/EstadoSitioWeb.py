# ProyectoA.com Aplicación Python para obtener el estado de un sitio web y devolver los datos en formato tentacle para Pandora FMS
# Versión 2.0

import argparse
import http.client
import ssl

# Clase para conectar con sitio web, devuelve en atributos el resultado de la conexión y el objeto conexionHTTP
class ConectarSitioWeb:
    urlRaiz = ""
    urlCompleta = ""
    puerto = None
    resultadoConexion = None
    conexionHTTP = None
    mensaje = ""
    
    # Constructor
    def __init__(self, urlRaiz, urlCompleta, puerto):
        self.urlRaiz = urlRaiz
        self.urlCompleta = urlCompleta
        self.puerto = puerto
    
    # Setters
    def setURLRaiz(self, url):
        self.urlRaiz = url
    def setURLCompleta(self, url):
        self.urlCompleta = url
    def setPuerto(self, puerto):
        self.puerto = puerto
        
    # Getters
    def getResultadoConexion (self):
        return self.resultadoConexion
    def getConexionHTTP (self):
        return self.conexionHTTP    
    def getMensaje (self):
        return self.mensaje
        
    # Método para conectar con sitio web (devolverá True si la conexión se ha realizado)
    def Conectar(self):
        # Para desactivar los mensajes de aviso de certificado para HTTPS
        ssl._create_default_https_context = ssl._create_unverified_context
        
        try:
            if self.puerto != None:
                conexionHTTP = http.client.HTTPSConnection(self.urlRaiz, self.puerto)
            else:
                conexionHTTP = http.client.HTTPSConnection(self.urlRaiz)
            conexionHTTP.request("GET", self.urlCompleta)
            resultadoConexion = conexionHTTP.getresponse()
            # Pasamos los valores devueltos a los atributos de la clase
            self.conexionHTTP = conexionHTTP
            self.resultadoConexion = resultadoConexion
            return True
        except Exception as ex:
            # Si se produce un error, mostraremos el error en la descripción del módulo 
            self.mensaje = "Error: {0}".format(getattr(ex, 'message', str(ex)))
            return False

# Mostrar resultado en consola con formato tentacle de Pandora FMS
def MostrarResultado(resultado, url, nombreModulo, mensaje):
    print("<module>")
    print("<name><![CDATA[{0}]]></name>".format(nombreModulo))
    print("<type><![CDATA[generic_proc]]></type>")
    print("<data><![CDATA[{0}]]></data>".format(resultado))
    print("<description><![CDATA[Comprobar estado {0}. {1}]]></description>".format(url, mensaje))
    # print("<unit>%</unit>")
    # print("<min_critical>95</min_critical>")
    # print("<max_critical>100</max_critical>")
    print("</module>")
    
# Mostrar y preparar los argumentos que admite el programa por la línea de comandos
def MostrarArgumentos():
    # Iniciamos el programa, obteniendo los argumentos pasados por la línea de comandos
    # Conformamos los argumentos que admitirá el programa por la línea de comandos
    parser = argparse.ArgumentParser()
    parser.add_argument("-ur", "--urlraiz", type=str, required=True,
        help="URL raíz a analizar (sin htt://)")
    parser.add_argument("-uc", "--urlcompleta", type=str, required=True,
        help="URL completa a analizar (con http o https://)")
    parser.add_argument("-p", "--puerto", type=int, required=False,
        help="Puerto de conexión")
    parser.add_argument("-m", "--modulo", type=str, required=True,
        help="Nombre del módulo")
    parser.add_argument("-v", "--version", action="store_true", required=False,
        help="Muestra por pantalla la versión de OpenSSL")
    parser.add_argument("-e", "--ComprobarPorEncabezado", action="store_true", required=False,
        help="Para obtener web activa usa un encabezado, necesita los parámetros -EncabezadoNombre -EncabezadoValor")
    parser.add_argument("-c", "--ComprobarPorCodigoRespuesta", action="store_true", required=False,
        help="Para obtener web activa usa un encabezado, necesita los parámetros -EncabezadoNombre -EncabezadoValor")    
    parser.add_argument("-en", "--EncabezadoNombre", type=str, required=False,
        help="Nombre del encabezado para obtener su valor y comprobar si es igual. Por ejemplo 'X-Redirect-By'. El valor del encabezado se indica en el parámetro -ev")
    parser.add_argument("-ev", "--EncabezadoValor", type=str, required=False,
        help="Valor del encabezado indicado en parámetro -en para comprobar si es igual, si lo es la web se marca como activa")
    parser.add_argument("-me", "--MostrarEncabezados", action="store_true", required=False,
        help="Devuelve todos los encabezados del sitio web y sus valores")
    
    return parser.parse_args()

# Comprobar el estado de la web por código de respuesta
def ComprobarEstadoWebCodigo(resultadoConexion, conexionHTTP, urlRaiz, modulo):
        # Códigos de estado que se consideran correctos
        # 200 OK            
        # 201 Created
        # 202 Accepted
        # 203 Non-Authoritative Information
        # 204 No Content
        # 205 Reset Content
        # 206 Partial Content
        # 207 Multi-Status (WebDAV)
        # 208 Already Reported (WebDAV)
        # 226 IM Used (HTTP Delta encoding)
        # 301 Moved Permanently
        # NOTA: si la web pasar por un WAF y no especificamos una URL con un fichero, tipo .../index.php, puede
        # que devuelva el estado 403 Forbidden        
    try:        
        if resultadoConexion.status in (200, 201, 202, 203, 204, 205, 206, 207, 208, 226, 301):
            resultado = 1
        else:
            resultado = 0
        # Establecemos el código de estado devuelto para mostrarlo en la descripción del módulo
        mensaje = "Codigo_Estado: {0}, Motivo: {1}".format(
            resultadoConexion.status, resultadoConexion.reason)
   
        MostrarResultado(resultado, urlRaiz, modulo, mensaje)
        
        # NOTA: si la web pasar por un WAF y no especificamos una URL con un fichero, tipo .../index.php, puede
        # que devuelva el estado 403 Forbidden
                
        conexionHTTP.close        
    except Exception as ex:
        # Si se produce un error, mostraremos el error en la descripción del módulo 
        MostrarResultado(0, urlRaiz, modulo, "Error: {0}".format(getattr(ex, 'message', str(ex))))

# Comprobar estado de la web por valor de cabecera: Date, Server, Upgrade, Connection, X-Powered-By, 
# Expires, Cache-Control, X-Redirect-By, Location, Content-Length, Content-Type, etc.
def ComprobarEstadoWebCabecera(resultadoConexion, conexionHTTP,
                               urlRaiz, modulo, cabecera, valorCabecera):
    try:
        # Obtenemos el valor de la cabecera pasada por parámetro        
        valorCabeceraDevuelto = resultadoConexion.getheader(cabecera)
        
        resultado = 0
        
        # Si no existe la cabecera, devolvemos error en el sitio web y pasamos en la descripción el motivo
        if valorCabeceraDevuelto is None:
            resultado = 0
            mensaje = "No se ha encontrado la cabecera: {0}".format(cabecera)
            conexionHTTP.close
        else:
            # Comprobamos si el valor de la cabecera obtenida del sitio web es igual al pasado por parámetro
            # Si es igual, el estado será correcto (1)
            compEncabezados = valorCabeceraDevuelto.upper() == valorCabecera.upper()

            if compEncabezados:
                resultado = 1
            else:
                resultado = 0
                
            conexionHTTP.close
            
            # Establecemos el valor de la cabecera devuelto para mostrarlo en la descripción del módulo
            mensaje = "Cabecera: {0}, Comparar: {1}, Devuelto: {2}".format(
                cabecera, valorCabecera, valorCabeceraDevuelto)
            
        # todasLasCabeceras = resultadoConexion.getheaders()
        # print(todasLasCabeceras)

        MostrarResultado(resultado, urlRaiz, modulo, mensaje)            
        
    except Exception as ex:
        # Si se produce un error, mostraremos el error en la descripción del módulo 
        MostrarResultado(0, urlRaiz, modulo, "Error: {0}".format(getattr(ex, 'message', str(ex))))
        
# Mostrar todos los encabezados (headers) del sitio web y sus valores
def ObtenerEncabezadosSitioWeb(resultadoConexion, conexionHTTP):
    try:
        # Obtenemos todos los encabezados (headers)
        return resultadoConexion.getheaders()
    except Exception as ex:
        return ""
    
# Procedimiento que ejecuta el resto de procedimientos para iniciar el programa
def IniciarPrograma():
    # Preparamos y mostramos los argumentos (si se indica)
    args = MostrarArgumentos()
    
    if args.version:
        print("Versión OpenSSL: {0}".format(ssl.OPENSSL_VERSION))
        
    if args.urlraiz and args.urlcompleta:
        urlRaiz = args.urlraiz
        urlCompleta = args.urlcompleta
        puerto = args.puerto
        
        # Instanciamos la clase ConectarSitioWeb
        conexion = ConectarSitioWeb(urlRaiz, urlCompleta, puerto)
        if conexion.Conectar():
            # Si se ha pasado el parámetro de mostrar encabezados -me
            # Mostramos los encabezados Headers del sitio web y su valor
            if args.MostrarEncabezados:
                print(ObtenerEncabezadosSitioWeb(conexion.getResultadoConexion(), conexion.getConexionHTTP()))
            else:
                # Si no se ha pasado el parámetro -me, comprobamos estado sitio web
                # Comprobamos que se haya pasado uno de los dos argumentos excluyentes:
                # -e (comprobar por Encabezado) o -c (Comprobar por código)
                comprobarCodigoRespuesta = False
                comprobarEncabezado = False
                if args.ComprobarPorCodigoRespuesta:
                    comprobarCodigoRespuesta = True
                if args.ComprobarPorEncabezado:
                    comprobarEncabezado = True
                continuar = False                
                # Si no se ha pasado ninguno de los dos parámetros de tipo de comprobación
                if not comprobarEncabezado and not comprobarCodigoRespuesta:
                    continuar = False
                    print("Debe añadir uno de los dos argumentos, o bien -e (comprobar por encabezado) o bien -c (comprobar por código)")
                if comprobarEncabezado or comprobarCodigoRespuesta:
                    continuar = True
                # No se admiten los dos parámetros -e o -c a la vez
                if comprobarEncabezado and comprobarCodigoRespuesta:
                    continuar = False
                    print("Debe indicar solo uno de los dos argumento, o bien -e o bien -c")                
                if continuar:
                    try:
                        # Si se comprueba si la web está activa por código de respuesta
                        if args.ComprobarPorCodigoRespuesta:
                            ComprobarEstadoWebCodigo(conexion.getResultadoConexion(), conexion.getConexionHTTP(),
                                                     urlRaiz, args.modulo)
                        
                        # Si se comprueba si la web está activa por código de respuesta
                        if args.ComprobarPorEncabezado:
                            continuar = True
                            # Si no se ha indicado el nombre del encabezado o el valor del encabezado, salir y avisar
                            if args.EncabezadoNombre is None:
                                print("Ha indicado la comprobación por encabezado (argumento -e) pero no ha indicado el nombre del encabezado (argumento -en)")
                                continuar = False
                            if args.EncabezadoValor is None:
                                print("Ha indicado la comprobación por encabezado (argumento -e) pero no ha indicado el valor del encabezado (argumento -ev)")
                                continuar = False
                            if continuar:
                                ComprobarEstadoWebCabecera(conexion.getResultadoConexion(), conexion.getConexionHTTP(), 
                                                           urlRaiz, args.modulo, args.EncabezadoNombre, args.EncabezadoValor)
                        
                    except Exception as ex:
                        # Si se produce un error, mostraremos el error en la descripción del módulo 
                        MostrarResultado(0, urlRaiz, args.modulo, "Error: {0}".format(getattr(ex, 'message', str(ex))))
        else:
            MostrarResultado(0, urlRaiz, args.modulo, conexion.getMensaje())        
    else:
        print("No ha indicado la URL raíz (parámetro -ur) o la URL completa (parámetro -uc)")             

# Iniciamos el programa
IniciarPrograma()