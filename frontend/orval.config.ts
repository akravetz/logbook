import { defineConfig } from "orval"

export default defineConfig({
  workoutApi: {
    input: "openapi.json",
    output: {
      mode: "single",
      target: "lib/api/generated.ts",
      schemas: "lib/api/model",
      client: "react-query",
      mock: false,
      override: {
        mutator: {
          path: "lib/api/mutator.ts",
          name: "customInstance",
        },
      },
    },
    hooks: {
      afterAllFilesWrite: "npx prettier --write",
    },
  },
})
