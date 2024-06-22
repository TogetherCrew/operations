console.log("Initializing database with init.js")
var rootUser = _getEnv('MONGO_INITDB_ROOT_USERNAME');
var rootPassword = _getEnv('MONGO_INITDB_ROOT_PASSWORD');
var admin = db.getSiblingDB('admin');
admin.auth(rootUser, rootPassword);
db.createUser({ user: rootUser, pwd: rootPassword, roles: ["readWrite"] });
console.log("Database initialized with init.js")