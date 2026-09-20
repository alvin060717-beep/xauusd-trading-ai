# XAUUSD Trading AI

Sistema de análisis y paper trading enfocado en XAUUSD.

## Ejecutar análisis local

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Windows: copy .env.example .env
python -m app.main
```

La aplicación funciona sin API externa usando datos sintéticos y una noticia demo. Para noticias reales, agrega `TRADINGECONOMICS_API_KEY` al archivo `.env`.

## Ejecutar API web

```bash
uvicorn app.api:app --reload
```

Abre `http://127.0.0.1:8000/docs`.

Endpoints:

- `GET /health` estado del servicio.
- `GET /analysis` análisis y decisión actual.
- `GET /news` eventos macro disponibles.
- `GET /account` balance de paper trading.
- `GET /trades` historial.
- `POST /paper/open` abre una operación solamente si la decisión es BUY o SELL.
- `POST /paper/close/{id}` cierra una operación; cuerpo: `{ "exit_price": 2350.0 }`.

## Nota sobre datos de mercado

La versión incluida genera velas sintéticas para probar el sistema. No debe usarse para operar dinero real. Antes de conectar un broker, reemplaza `MarketData` por un adaptador autenticado de tu broker y valida los resultados con backtesting y paper trading.
