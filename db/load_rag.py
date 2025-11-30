import json
from langchain_openai import OpenAIEmbeddings
from db.connection import SessionLocal
from db.rag import KnowledgeDoc
import settings

# Define the 4 Master Documents based on specs/rag_info.md
DOCS = {
    "locations": """
# Sedes y Horarios de Kavak
Kavak cuenta con 15 sedes y 13 centros de inspección en México.

## Puebla
- **Kavak Explanada**: Calle Ignacio Allende 512, Santiago Momoxpan, KAVAK Puebla, Puebla, 72760. Lun-Sab 9-6, Dom 9-6.
- **Kavak Las Torres**: Blvd. Municipio Libre 1910, Ex Hacienda Mayorazgo, 72480 Puebla, Puebla.

## Monterrey
- **Kavak Punto Valle**: Rio Missouri 555, Del Valle, 66220 San Pedro Garza García, N.L. Sótano 4.
- **Kavak Nuevo Sur**: Avenida Revolución 2703, Colonia Ladrillera, Monterrey, Nuevo León, CP: 64830.

## Ciudad de México (CDMX)
- **Plaza Fortuna**: Av Fortuna 334, Magdalena de las Salinas, 07760.
- **Patio Santa Fe**: Plaza Patio Santa Fe, Sótano 3. Vasco de Quiroga 200-400, Santa Fe, Zedec Sta Fé, 01219.
- **Tlalnepantla**: Sentura Tlalnepantla, Perif. Blvd. Manuel Ávila Camacho 1434, San Andres Atenco, 54040.
- **El Rosario**: Av. El Rosario No. 1025 Esq. Av. Aquiles Serdán, sótano 3, Col. El Rosario, C.P. 02100, Azcapotzalco.
- **Cosmopol**: Av. José López Portillo 1, Bosques del Valle, 55717 San Francisco Coacalco, Méx.
- **Antara**: Sótano -3 Av Moliere, Polanco II Secc, Miguel Hidalgo, 11520.
- **Artz Pedregal**: Perif. Sur 3720, Jardines del Pedregal, Álvaro Obregón, 01900.

## Guadalajara
- **Midtown**: Av Adolfo López Mateos Nte 1133, Italia Providencia, 44648 Guadalajara, Jal.
- **Punto Sur**: Av. Punto Sur # 235, Los Gavilanes, 45645 Tlajomulco de Zúñiga, Jal. Sótano 2 Deck Norte.

## Querétaro
- **Puerta la Victoria**: Av. Constituyentes Número 40 Sótano 3, Col. Villas del Sol, Querétaro, Qro. 76040.

## Cuernavaca
- **Forum Cuernavaca**: Jacarandas 103, Ricardo Flores Magon, Cuernavaca. México. 62370.

## Toluca
- **Kavak Toluca**: Ven y conoce la sede de esta empresa en Toluca.
""",

    "financing": """
# Financiamiento y Pagos a Meses
Kavak ofrece planes de pago a meses para comprar tu auto.

## Cómo funciona el plan de pago a meses
1. **Solicita tu plan**: Conoce en menos de 2 minutos las opciones que tenemos para ti.
2. **Completa los datos**: Ingresa tu información y valídala para recibir tu plan de pagos.
3. **Realiza el primer pago**: Asegura tu compra y domicilia los pagos mensuales.
4. **Agenda la entrega**: Firma el contrato y recibe las llaves de tu próximo auto.

## Requisitos (Documentación)
- **Identificación oficial (INE/Pasaporte)**: Copia legible vigente.
- **Comprobante de domicilio**: Reciente (luz, agua, gas) con nombre completo y dirección actual.
- **Comprobantes de ingresos**: Recibos de nómina o estados de cuenta (3 meses) para evaluar capacidad de pago.

## Condiciones Generales
- Tasa de interés base: ~10% anual.
- Plazos: 3 a 6 años (36 a 72 meses).
- Enganche: Personalizable.
""",

    "buying_selling": """
# Compra y Venta de Autos y Beneficios

## Beneficios de Kavak
- **Mejor precio**: Excelentes precios en miles de autos usados.
- **Autos 100% certificados**: Inspección integral de 240 puntos (exterior, interior, motor).
- **Todo digital o en sedes**: Trámites sin salir de casa o en centros de atención.

## Vender tu auto a Kavak
Kavak ofrece 3 tipos de ofertas según la demanda:
1. **Oferta al instante (Pago inmediato)**: Si te urge el dinero.
2. **Pago a 30 días**: Monto mayor, pero esperas un mes.
3. **Consignación (Pago al vender)**: Dejas el auto y te pagan cuando se venda (mejor oferta si no necesitas el dinero ya).

**Proceso de Venta**:
- Cotiza en línea.
- Agenda inspección.
- Si pasa, recibes el pago según la oferta.
- **Trade-in**: Puedes dejar tu auto a cuenta para comprar otro.

## Comprar un auto
- Catálogo en línea en kavak.com.
- Cita por videollamada para ver detalles.
- Entrega a domicilio o en sede.
""",

    "warranty": """
# Garantía y Post-venta
## Periodo de Prueba
- **7 días o 300 km**: Si no te convence, lo devuelves y te reembolsan (o cambias por otro).

## Garantía
- **3 meses incluidos**: Cobertura básica.
- **Kavak Total**: Puedes extenderla por un año más (costo extra).
""",

    "app_services": """
# App Kavak y Servicios de Mantenimiento
## App Kavak
Desde la app puedes:
- Agendar mantenimiento.
- Consultar trámites.
- Aplicar garantía.
- Cotizar tu auto.
- Ampliar garantía a Kavak Total.

## Mantenimiento
Es muy sencillo agendar un servicio de mantenimiento desde tu App Kavak:
1. Ingresa con tu correo y contraseña.
2. Ve al apartado "Servicios de mantenimiento".
3. Elige el servicio: **básico, media o larga vida**.

*Recuerda que con Kavak Total cuentas con dos servicios básicos incluidos a partir de tu sexto mes.*
""",

    "general_info": """
# Acerca de Kavak
## Kavak Unicornio Mexicano
Kavak México ha logrado un estatus como empresa unicornio en el país.
- **Historia**: Nació en el DF y se expandió a toda la república.
- **Misión**: Ofrecer una solución para los mexicanos que luchaban al comprar o vender un auto seminuevo, siendo un aliado confiable que gestiona trámites y ofrece beneficios reales.
- **Cobertura**: 15 sedes y 13 centros de inspección cubriendo casi todo el territorio nacional.
"""
}

def load_data():
    print("Generando embeddings y cargando datos...")
    embeddings_model = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY
    )
    
    db = SessionLocal()
    
    # Clear existing data
    db.query(KnowledgeDoc).delete()
    
    for category, content in DOCS.items():
        print(f"Procesando: {category}...")
        # Generate embedding for the content + category name to boost retrieval
        text_to_embed = f"{category.replace('_', ' ')}\n{content}"
        vector = embeddings_model.embed_query(text_to_embed)
        
        doc = KnowledgeDoc(
            category=category,
            content=content,
            embedding=json.dumps(vector)
        )
        db.add(doc)
    
    db.commit()
    db.close()
    print("Carga completada exitosamente.")

if __name__ == "__main__":
    load_data()
