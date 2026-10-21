"""Bounded contexts. Each module owns its router, service, repository, models and schemas.

Modules talk to each other through services, never through another module's repository or models.
"""
