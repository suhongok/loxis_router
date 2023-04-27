import sys
import socket
import loxis_method as method
import loxis_common as common
##Basic Method----------------------------------##




##Main Function-----------------------------------##
def main(arg):
    router = method.Router()##local router setup
    router.start()##start router

main(arg=sys.argv)