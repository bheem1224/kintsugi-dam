import wasmtime
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
module = wasmtime.Module(engine, "(module (memory (export \"memory\") 1))")
linker = wasmtime.Linker(engine)
instance = linker.instantiate(store, module)
memory = instance.exports(store)["memory"]
print(dir(memory))
print(memory.size(store))
print(memory.data_len(store))
