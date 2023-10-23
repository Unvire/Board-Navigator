import camcadFileLoader
import gencadFileLoader
import obpPlusPlusv7FileLoader
import os

class SchematicLoader():
    @staticmethod
    def loadSchematic(name, path='Schematic'):
        filePath = os.path.join(os.getcwd(), path, name)
        if '.tgz' in name:
            schematic = obpPlusPlusv7FileLoader.OdbPlusPlusv7FileLoader()
            return schematic.loadSchematic(name, path)
        else:
            with open(filePath, 'r') as file:
                char = file.read(1)
                if char == ';':
                    schematic = camcadFileLoader.CamCADLoader()
                    return schematic.loadSchematic(name, path)
                elif char == '$':
                    schematic = gencadFileLoader.GenCADLoader()
                    return schematic.loadSchematic(name, path)

if __name__ == '__main__':
    data = SchematicLoader.loadSchematic('nexyM.gcd')
    print(data[1]['GND'])
    SchematicLoader.loadSchematic('gemis2.cad')
    SchematicLoader.loadSchematic('odb_15020617_01.tgz')
