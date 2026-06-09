"""Unified entry point — runs all services in a single process."""

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    from registry.__main__ import serve as serve_registry
    from customer_agent.__main__ import serve as serve_customer
    from law_agent.__main__ import serve as serve_law
    from tax_agent.__main__ import serve as serve_tax
    from compliance_agent.__main__ import serve as serve_compliance
    from demo_web.__main__ import serve as serve_demo

    logger.info("Starting Registry on port 10000...")
    reg_task = asyncio.create_task(serve_registry(10000))
    await asyncio.sleep(3)

    logger.info("Starting all agents and web demo...")
    tasks = [
        asyncio.create_task(serve_customer(10100)),
        asyncio.create_task(serve_law(10101)),
        asyncio.create_task(serve_tax(10102)),
        asyncio.create_task(serve_compliance(10103)),
        asyncio.create_task(serve_demo(8080)),
    ]

    print("")
    print("============================================")
    print("  All services running in a single process")
    print("  Web Demo: http://localhost:8080")
    print("  Press Ctrl+C to stop")
    print("============================================")
    print("")

    try:
        await asyncio.gather(reg_task, *tasks)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())
