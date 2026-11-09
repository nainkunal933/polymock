# Examples

## Blog

A SQL Server blog schema with users, posts, comments, and interactions.
Includes CRUD stored procedures for each table.

### Run locally

With Docker running Linux containers, execute from the repository root in PowerShell:

```powershell
docker build --pull -t polymock-blog ./examples/blog
$env:MSSQL_SA_PASSWORD = '<strong-password>'
docker run --name polymock-blog -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD -p 127.0.0.1:1433:1433 -d polymock-blog
docker logs -f polymock-blog
```

Replace `<strong-password>` with your own password. SQL Server requires at least
eight characters from three of these groups: uppercase, lowercase, digits, and
symbols.

## Shopping cart

A MongoDB shopping cart schema with carts, orders, and products.
Creates collections with JSON Schema validators on startup.

### Run locally

With Docker running Linux containers, execute from the repository root in PowerShell:

```powershell
docker build --pull -t polymock-shopping-cart ./examples/shopping_cart
docker run --name polymock-shopping-cart -p 127.0.0.1:27017:27017 -d polymock-shopping-cart
docker logs -f polymock-shopping-cart
```
