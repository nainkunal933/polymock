FROM mcr.microsoft.com/mssql/server:2025-latest

COPY --chown=mssql:mssql data/tables/ /schema/tables/
COPY --chown=mssql:mssql init.sql entrypoint.sh /schema/

# Strip Windows line endings from a checkout made on Windows.
USER root
RUN sed -i 's/\r$//' /schema/entrypoint.sh
USER mssql

ENTRYPOINT ["/bin/bash", "/schema/entrypoint.sh"]
CMD ["/opt/mssql/bin/sqlservr"]
