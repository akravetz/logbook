variable "envfile" {
    type    = string
    default = ".env"
}

locals {
    envfile = {
        for line in split("\n", file(var.envfile)): split("=", line)[0] => regex("=(.*)", line)[0]
        if !startswith(line, "#") && length(split("=", line)) > 1
    }
}

data "external_schema" "sqlalchemy" {
    program = [
        "uv", "run", "python",
        "scripts/load_models.py"
    ]
}

env "local" {
    src = data.external_schema.sqlalchemy.url
    url = local.envfile["DATABASE_URL"]
    dev = "docker://postgres/16/dev?search_path=public"
    migration {
        dir = "file://migrations"
    }
    format {
        migrate {
            diff = "{{ sql . \"  \" }}"
        }
    }
}

env "prod" {
    src = data.external_schema.sqlalchemy.url
    url = local.envfile["PROD_DATABASE_URL"]
    dev = "docker://postgres/16/dev?search_path=public"
    migration {
        dir = "file://migrations"
    }
    format {
        migrate {
            diff = "{{ sql . \"  \" }}"
        }
    }
}
