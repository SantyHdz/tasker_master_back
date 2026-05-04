# Instrucciones para Configurar el Workflow de n8n

## Problemas Corregidos

He corregido los siguientes problemas en el workflow:

1. **Eliminado autenticación HTTP**: Removí las credenciales que causaban errores
2. **URLs directas**: Cambié de `{{ $env.API_BASE_URL }}` a `http://localhost:8000`
3. **Expresiones corregidas**: Ajusté las expresiones para que funcionen en n8n
4. **Simplificación**: Removí configuraciones complejas que causaban errores

## Pasos para Importar y Configurar

### 1. Importar el Workflow

1. **En n8n**, ve a **Workflows** → **Import from File**
2. **Selecciona el archivo**: `N8N_WORKFLOW_CORRECTED.json`
3. **Haz clic en Import**

### 2. Configurar la URL de la API

El workflow ya está configurado con tu backend en **Render**: `https://tasker-master-backend.onrender.com`

**URLs configuradas:**
- `https://tasker-master-backend.onrender.com/tasks/notifications/pending`
- `https://tasker-master-backend.onrender.com/tasks/{{ $json.id }}/notifications/24h`
- `https://tasker-master-backend.onrender.com/tasks/{{ $json.id }}/notifications/1h`
- `https://tasker-master-backend.onrender.com/tasks/{{ $json.id }}/notifications/10m`

**No necesitas cambiar nada** si tu backend está en `https://tasker-master-backend.onrender.com`

### 3. Verificar las Credenciales de Telegram

Las credenciales de Telegram ya están configuradas con tu ID existente (`s4ejytIPJxjeTZHw`).

### 4. Probar el Workflow

1. **Asegúrate de que tu API esté corriendo** en el puerto configurado
2. **Crea una tarea de prueba** con una fecha de vencimiento en las próximas 24 horas
3. **Ejecuta el workflow manualmente** en n8n
4. **Verifica que**:
   - El nodo "Get Pending Tasks" devuelve datos
   - Los nodos IF detectan las tareas correctamente
   - Se envían los mensajes de Telegram
   - Los nodos "Mark Sent" actualizan los flags

## Configuración de URLs por Ambiente

### Producción (Render) ✅ **CONFIGURADO**
```
https://tasker-master-backend.onrender.com
```

### Desarrollo (Local)
```
http://localhost:8000
```

### Staging
```
https://staging.tu-dominio.com
```

**Nota**: El workflow ya está configurado para producción en Render. Si necesitas cambiar a otro ambiente, edita las URLs en los nodos HTTP Request.

## Solución de Problemas Comunes

### Error: "not accessible via UI, please run node"

**Causa**: Las expresiones en el workflow no se pueden evaluar en la UI.

**Solución**:
1. Ejecuta el workflow manualmente una vez
2. Las expresiones se evaluarán durante la ejecución
3. Verifica los resultados en la pestaña de ejecución

### Error: "Connection refused"

**Causa**: La API no está corriendo o la URL es incorrecta.

**Solución**:
1. Verifica que tu API esté corriendo: `uvicorn app.main:app --reload`
2. Confirma la URL correcta en los nodos HTTP Request
3. Prueba la URL manualmente en el navegador

### Error: "No tasks returned"

**Causa**: No hay tareas que cumplan con los criterios de notificación.

**Solución**:
1. Crea una tarea con `due_date` en las próximas 24 horas
2. Asegúrate de que `is_completed` sea `false`
3. Verifica que los flags de notificación (`notified_24h`, etc.) sean `false`

### Error: "Telegram message not sent"

**Causa**: Problemas con las credenciales de Telegram o el chat ID.

**Solución**:
1. Verifica que el bot de Telegram tenga permisos
2. Confirma que el chat ID `5550201252` sea correcto
3. Prueba enviar un mensaje manualmente desde n8n

## Estructura del Workflow

```
Schedule Trigger (cada 5 minutos)
    ↓
Get Pending Tasks (GET /tasks/notifications/pending)
    ↓
    ├─→ Check 24h → Set Tasks → Split → Send Telegram → Mark Sent
    ├─→ Check 1h  → Set Tasks → Split → Send Telegram → Mark Sent
    └─→ Check 10m → Set Tasks → Split → Send Telegram → Mark Sent
```

## Personalización

### Cambiar el Intervalo de Ejecución

1. **Abre el nodo "Schedule Trigger"**
2. **Cambia "minutesInterval"** de 5 a otro valor
3. **Recomendado**: 5 minutos para balance entre respuesta y rendimiento

### Cambiar los Mensajes de Telegram

1. **Abre los nodos "Send Telegram 24h/1h/10m"**
2. **Edita el campo "text"**
3. **Usa las variables disponibles**:
   - `{{ $json.title }}` - Título de la tarea
   - `{{ $json.description }}` - Descripción
   - `{{ $json.due_date }}` - Fecha de vencimiento
   - `{{ $json.priority_id }}` - Prioridad

### Agregar Autenticación (Opcional)

Si necesitas agregar autenticación a la API:

1. **Crea credenciales en n8n**:
   - Credentials → New Credential → Header Auth
   - Configura el header de autenticación

2. **Agrega autenticación a los nodos HTTP**:
   - Abre cada nodo HTTP Request
   - Habilita "Authentication"
   - Selecciona "Generic Credential Type" → "Header Auth"
   - Selecciona tus credenciales

## Monitoreo

### Verificar Ejecuciones

1. **Ve a la pestaña "Executions"** en n8n
2. **Revisa las ejecuciones del workflow**
3. **Verifica que no haya errores**

### Logs Importantes

- **Get Pending Tasks**: Debe devolver tareas en las categorías 24h, 1h, 10m
- **Check Notifications**: Debe detectar tareas correctamente
- **Send Telegram**: Debe mostrar mensajes enviados exitosamente
- **Mark Sent**: Debe mostrar actualizaciones exitosas

## Pruebas

### Prueba 1: Tarea en 24 horas
1. Crea una tarea con `due_date` en 23-25 horas
2. Ejecuta el workflow
3. Verifica que se envíe el mensaje de 24h
4. Confirma que `notified_24h` sea `true`

### Prueba 2: Tarea en 1 hora
1. Crea una tarea con `due_date` en 55-65 minutos
2. Ejecuta el workflow
3. Verifica que se envíe el mensaje de 1h
4. Confirma que `notified_1h` sea `true`

### Prueba 3: Tarea en 10 minutos
1. Crea una tarea con `due_date` en 8-12 minutos
2. Ejecuta el workflow
3. Verifica que se envíe el mensaje de 10m
4. Confirma que `notified_10m` sea `true`

## Soporte

Si encuentras algún problema:

1. **Revisa los logs de ejecución** en n8n
2. **Verifica que la API esté corriendo**
3. **Confirma la configuración de URLs**
4. **Prueba los endpoints de la API manualmente**

## Archivos Relacionados

- `N8N_WORKFLOW_CORRECTED.json` - Workflow corregido
- `N8N_WORKFLOW_GUIDE.md` - Guía completa del workflow
- `CLAUDE.md` - Documentación del proyecto