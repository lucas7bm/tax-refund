#from flask import Flask
#from flask_restful import Api, Resource
#import extract

#app = Flask(__name__)
#api = Api(app)

#class Extract(Resource):
#    def get(self):
#        extract.from_pdf("./")
#        return
#        
#    def put(self, files):
#        for file in files:
#            print(file)

#api.add_resource(Extract, "/extract")

#if __name__ == "__main__":
#    app.run(debug=True)