# 🎭 DHCP Spoofing Attack — Seguridad de Redes

<div align="center">

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Scapy](https://img.shields.io/badge/Scapy-Latest-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Linux-orange?style=for-the-badge&logo=linux)
![License](https://img.shields.io/badge/Uso-Educativo-red?style=for-the-badge)

**Sael Germán García** | Matrícula: `2025-0725`  
Asignatura: Seguridad de Redes | Profesor: Jonathan Rondón  
Instituto Tecnológico de las Américas — ITLA | 2026

</div>

---

## 📋 Descripción del Ataque

El **DHCP Spoofing Attack** explota la carencia de mecanismos de autenticación nativos en el protocolo **DHCP (Dynamic Host Configuration Protocol)**. Se implementa un **Rogue DHCP Server** que intercepta las solicitudes DHCP Discover de los clientes legítimos y les provee parámetros de red maliciosos, logrando secuestrar el enrutamiento y la resolución de nombres DNS hacia el nodo atacante.

> 💡 **Prerrequisito:** Para escuchar Broadcasts de múltiples VLANs simultáneamente, el puerto del atacante (e0/3 en SW1) se configura en modo **Trunk 802.1Q** con subinterfaces virtuales.

---

## 🗺️ Topología de Red

### 📊 Segmentación de VLANs

| VLAN ID | Nombre | Segmento IP | Descripción |
|:-------:|:------:|:-----------:|-------------|
| 10 | Usuarios | 10.7.25.0/24 | VPC1 — Pool atacado, GW malicioso: 10.7.25.50 |
| 20 | Servidores | 10.7.20.0/24 | VPC2 — Pool atacado, GW malicioso: 10.7.20.50 |
| Trunk | Inter-VLAN | Múltiple | e0/3 de SW1 en modo Trunk para el atacante |

### 📊 Matriz de Direccionamiento

| Elemento | Dirección IP | Interfaz | Detalle |
|:--------:|:------------:|:--------:|---------|
| DHCP Legítimo (R1) | 10.7.25.1 / 10.7.20.1 | Eth0/0.10 y .20 | Servicio en pausa durante el ataque |
| Atacante VLAN 10 | 10.7.25.50 | ens4.10 | Responde Broadcasts en VLAN 10 |
| Atacante VLAN 20 | 10.7.20.50 | ens4.20 | Responde Broadcasts en VLAN 20 |
| Víctima Comprometida | 10.7.20.100 | VPC | Obtiene IP del pool malicioso vía DORA |

---

## ⚙️ Requisitos

```bash
# Sistema Operativo
Ubuntu Linux (recomendado)

# Dependencias
sudo apt update && sudo apt install -y python3-scapy python3-pip

# Privilegios requeridos
sudo / root
```

---

## 🔧 Configuración Previa

### Habilitar Trunk en SW1
```cisco
SW1(config)# interface ethernet0/3
SW1(config-if)# switchport trunk encapsulation dot1q
SW1(config-if)# switchport mode trunk
SW1(config-if)# no shutdown
SW1(config-if)# end
SW1# write memory
```

### Crear subinterfaces 802.1Q en el atacante
```bash
sudo ip link add link ens4 name ens4.10 type vlan id 10
sudo ip link add link ens4 name ens4.20 type vlan id 20
sudo ip link set ens4.10 up
sudo ip link set ens4.20 up
sudo ip addr add 10.7.25.50/24 dev ens4.10
sudo ip addr add 10.7.20.50/24 dev ens4.20
```

---

## 🚀 Uso

```bash
# Ejecutar el servidor DHCP malicioso
sudo python3 dhcp_spoofing.py

# Verificar en la víctima (VPC1 o VPC2)
ip dhcp

# Resultado esperado
DORA IP 10.7.25.100/24 GW 10.7.25.50  ← Gateway del atacante
```

---

## 🔬 ¿Cómo funciona?

| Paso | Descripción |
|:----:|-------------|
| 1️⃣ | `IP_CONFIG` — Mapea cada subinterfaz con su pool malicioso, GW y DNS falsos |
| 2️⃣ | `sniff_iface()` — Lanza un hilo independiente por cada VLAN con filtro BPF en puertos 67/68 |
| 3️⃣ | `handle_dhcp()` — Al recibir **Discover**, responde con **Offer** malicioso (IP atacante como GW y DNS) |
| 4️⃣ | Al recibir **Request**, valida el `server_id` y despacha el **ACK** definitivo |
| 5️⃣ | Completa el proceso **DORA** — la víctima queda enrutada por el atacante |

---

## 🛡️ Contramedidas

### 1. Habilitar DHCP Snooping globalmente
```cisco
SW1(config)# ip dhcp snooping
SW1(config)# ip dhcp snooping vlan 10,20
```

### 2. Configurar puerto confiable hacia R1
```cisco
SW1(config)# interface ethernet0/0
SW1(config-if)# ip dhcp snooping trust
SW1(config-if)# exit
```

### 3. Limitar tasa de peticiones DHCP (previene Starvation)
```cisco
SW1(config)# interface range ethernet0/1-3
SW1(config-if-range)# ip dhcp snooping limit rate 15
```

---

## 📁 Archivos del Repositorio

| Archivo | Descripción |
|:-------:|-------------|
| [`dhcp_spoofing.py`](dhcp_spoofing.py) | Script principal del ataque |
| [`SaelGermanGarcia_2025-0725_DHCP_Spoofing_Informe_P1.pdf`](SaelGermanGarcia_2025-0725_DHCP_Spoofing_Informe_P1.pdf) | Documentación técnica completa |

---

## 🖼️ Capturas de Pantalla

- 📸 [Hilos de escucha y envío de DHCP Offers/ACKs](Capturas%20de%20pantalla%20DHCP%20Spoofing/Los%20hilos%20de%20escucha%20y%20el%20env%C3%ADo%20de%20DHCP%20OffersACKs%20.png)
- 📸 [Secuestro de Enrutamiento — Asignación DHCP Maliciosa](Capturas%20de%20pantalla%20DHCP%20Spoofing/Secuestro%20de%20Enrutamiento%20mediante%20Asignaci%C3%B3n%20DHCP%20Maliciosa.png)
- 📸 [Contramedida Aplicada](Capturas%20de%20pantalla%20DHCP%20Spoofing/contramedidas.png)

---

## 📎 Recursos

📄 **Documentación Técnica:** [Ver Informe PDF](SaelGermanGarcia_2025-0725_DHCP_Spoofing_Informe_P1.pdf)  
▶️ **Video Demostración:** [Ver en YouTube](https://youtube.com/playlist?list=PLV_dKVnYXf6dpmk3j8uXPHAZdbrkCQGAY)

---

## 📚 Referencias

1. Cisco Systems. *DHCP Snooping Configuration Guide*. Documentación oficial de Cisco IOS.
2. Scapy Project. *Scapy: Interactive packet manipulation program*. [https://scapy.net/](https://scapy.net/)
3. IETF. *RFC 2131: Dynamic Host Configuration Protocol*. Especificación base del protocolo DHCP.
4. Reconocimiento especial: Troubleshooting, base del script y documentación apoyado en Inteligencia Artificial.

---

<div align="center">

⚠️ **AVISO LEGAL** ⚠️  
*Este script fue desarrollado exclusivamente con fines académicos y educativos.*  
*Su uso en redes sin autorización explícita es ilegal y éticamente inaceptable.*

</div>
