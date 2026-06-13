/*
 * Sistema de Clasificación de Limones - Control de Seleccionadoras
 * Arduino Sketch para controlar 5-6 salidas (seleccionadoras en banda transportadora)
 * 
 * Protocolo Serial:
 * - Comando: "S<num>D<ms>\n"
 * - Ejemplo: "S1D500\n" → Activar salida 1 por 500ms
 * - Respuesta: "OK:S1D500\n"
 * 
 * Hardware requerido:
 * - Arduino Mega/Uno
 * - Módulo de relés de 8 canales (5V)
 * - Fuente de alimentación externa para relés
 * 
 * Conexiones:
 * - Relé 1 → Pin 2 (Brasil)
 * - Relé 2 → Pin 3 (Europa)
 * - Relé 3 → Pin 4 (Local Premium)
 * - Relé 4 → Pin 5 (Industrial)
 * - Relé 5 → Pin 6 (Descarte)
 * - Relé 6 → Pin 7 (Reserva)
 */

// Configuración de pines
const int NUM_SALIDAS = 6;
const int PINES_SALIDA[] = {2, 3, 4, 5, 6, 7};  // Pines digitales

// LED integrado para feedback visual
const int PIN_LED = LED_BUILTIN;

// Buffer para comandos seriales
String comandoBuffer = "";
boolean comandoCompleto = false;

void setup() {
  // Inicializar serial
  Serial.begin(9600);
  while (!Serial) {
    ; // Esperar conexión (solo necesario en algunas placas)
  }
  
  // Configurar pines como salidas
  for (int i = 0; i < NUM_SALIDAS; i++) {
    pinMode(PINES_SALIDA[i], OUTPUT);
    digitalWrite(PINES_SALIDA[i], LOW);  // Relés OFF (asumiendo lógica activa HIGH)
  }
  
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  
  // Mensaje de inicio
  Serial.println("ARDUINO_READY");
  Serial.println("Sistema de Clasificacion de Limones v1.0");
  Serial.print("Salidas disponibles: ");
  Serial.println(NUM_SALIDAS);
  
  // Test de salidas (secuencia de bienvenida)
  for (int i = 0; i < NUM_SALIDAS; i++) {
    digitalWrite(PINES_SALIDA[i], HIGH);
    digitalWrite(PIN_LED, HIGH);
    delay(100);
    digitalWrite(PINES_SALIDA[i], LOW);
    digitalWrite(PIN_LED, LOW);
    delay(50);
  }
  
  Serial.println("READY");
}

void loop() {
  // Leer comandos seriales
  if (comandoCompleto) {
    procesarComando(comandoBuffer);
    comandoBuffer = "";
    comandoCompleto = false;
  }
}

// Interrupción serial
void serialEvent() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    
    if (c == '\n') {
      comandoCompleto = true;
    } else {
      comandoBuffer += c;
    }
  }
}

void procesarComando(String comando) {
  comando.trim();  // Eliminar espacios
  
  // Formato esperado: "S<num>D<ms>"
  // Ejemplo: "S1D500"
  
  if (comando.startsWith("S") && comando.indexOf("D") > 0) {
    // Extraer número de salida
    int posD = comando.indexOf("D");
    String numStr = comando.substring(1, posD);
    int numeroSalida = numStr.toInt();
    
    // Extraer duración
    String duracionStr = comando.substring(posD + 1);
    int duracion = duracionStr.toInt();
    
    // Validar
    if (numeroSalida >= 1 && numeroSalida <= NUM_SALIDAS && duracion > 0 && duracion <= 5000) {
      activarSalida(numeroSalida, duracion);
      
      // Enviar confirmación
      Serial.print("OK:");
      Serial.println(comando);
    } else {
      Serial.print("ERROR:INVALID_PARAMS:");
      Serial.println(comando);
    }
  } 
  else if (comando == "STATUS") {
    // Comando de estado
    Serial.println("STATUS:OK");
    Serial.print("SALIDAS:");
    Serial.println(NUM_SALIDAS);
  }
  else if (comando == "TEST") {
    // Test de todas las salidas
    Serial.println("TEST:START");
    for (int i = 1; i <= NUM_SALIDAS; i++) {
      activarSalida(i, 200);
      delay(300);
    }
    Serial.println("TEST:COMPLETE");
  }
  else {
    Serial.print("ERROR:UNKNOWN_CMD:");
    Serial.println(comando);
  }
}

void activarSalida(int numeroSalida, int duracion) {
  int pin = PINES_SALIDA[numeroSalida - 1];  // Ajustar índice
  
  // Activar
  digitalWrite(pin, HIGH);
  digitalWrite(PIN_LED, HIGH);
  
  Serial.print("ACTIVADO:S");
  Serial.print(numeroSalida);
  Serial.print(":PIN");
  Serial.print(pin);
  Serial.print(":");
  Serial.print(duracion);
  Serial.println("ms");
  
  // Esperar duración
  delay(duracion);
  
  // Desactivar
  digitalWrite(pin, LOW);
  digitalWrite(PIN_LED, LOW);
  
  Serial.print("DESACTIVADO:S");
  Serial.println(numeroSalida);
}

/*
 * PROTOCOLO DE COMUNICACIÓN:
 * 
 * PC envía → Arduino:
 * - "S1D500\n"  → Activar salida 1 por 500ms
 * - "S2D1000\n" → Activar salida 2 por 1000ms
 * - "STATUS\n"  → Solicitar estado
 * - "TEST\n"    → Test de todas las salidas
 * 
 * Arduino responde → PC:
 * - "OK:S1D500\n"           → Comando ejecutado
 * - "ERROR:INVALID_PARAMS\n" → Parámetros inválidos
 * - "ACTIVADO:S1:PIN2:500ms\n" → Info de activación
 * - "DESACTIVADO:S1\n"       → Info de desactivación
 * - "STATUS:OK\n"            → Estado OK
 * - "SALIDAS:6\n"            → Número de salidas
 * 
 * NOTAS:
 * - Baudrate: 9600 bps
 * - Final de línea: \n (LF)
 * - Duración máxima: 5000ms (5 segundos)
 * - Salidas: 1 a 6 (ajustable en NUM_SALIDAS)
 */
