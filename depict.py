import xml.etree.ElementTree as ET
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from cdkmodules import getCDKSDG
import jpype
from jpype import JClass
import numpy as np
from PIL import Image


def getCDKDepiction(smiles: str, molSize=(512, 512), rotate=0, unicolor=False):
    """This function takes the user input SMILES and Depicts it
       using the CDK Depiction Generator.
    Args:
            smiles (string): SMILES string given by the user.
    Returns:
            image (SVG): CDK Structure Depiction as a SVG image.
    """
    cdk_base = "org.openscience.cdk"
    StandardGenerator = JClass(
        cdk_base + ".renderer.generators.standard.StandardGenerator"
    )
    Color = JClass("java.awt.Color")
    UniColor = JClass(cdk_base + ".renderer.color.UniColor")
    CDK2DAtomColors = JClass(cdk_base + ".renderer.color.CDK2DAtomColors")()
    if unicolor:
        DepictionGenerator = (
            JClass(cdk_base + ".depict.DepictionGenerator")()
            .withSize(molSize[0], molSize[1])
            .withAtomValues()
            .withParam(StandardGenerator.StrokeRatio.class_, 1.0)
            .withAnnotationColor(Color.BLACK)
            .withParam(StandardGenerator.AtomColor.class_, UniColor(Color.BLACK))
            .withBackgroundColor(Color.WHITE)
            .withFillToFit()
        )
    else:
        DepictionGenerator = (
            JClass(cdk_base + ".depict.DepictionGenerator")()
            .withAtomColors(CDK2DAtomColors)
            .withSize(molSize[0], molSize[1])
            .withAtomValues()
            .withParam(StandardGenerator.StrokeRatio.class_, 1.0)
            .withFillToFit()
            .withBackgroundColor(Color.WHITE)
        )
    if any(char.isspace() for char in smiles):
        smiles = smiles.replace(" ", "+")

    moleculeSDG = getCDKSDG(smiles)

    if moleculeSDG:

        # Rotate molecule
        point = JClass(cdk_base + ".geometry.GeometryTools").get2DCenter(moleculeSDG)
        JClass(cdk_base + ".geometry.GeometryTools").rotate(
            moleculeSDG, point, (rotate * JClass("java.lang.Math").PI / 180.0)
        )

        mol_imageSVG = DepictionGenerator.depict(moleculeSDG).toImg()
        java_buffered_image = mol_imageSVG  # Your Java BufferedImage object
        width = java_buffered_image.getWidth()
        height = java_buffered_image.getHeight()
        pixels = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                pixel = java_buffered_image.getRGB(x, y)
                red = (pixel >> 16) & 0xFF
                green = (pixel >> 8) & 0xFF
                blue = pixel & 0xFF
                pixels[y, x] = [red, green, blue]

        # Create a Pillow Image object from the numpy array
        image = Image.fromarray(pixels)

        return image
    else:
        return "Error reading SMILES string, check again."


def getRDKitDepiction(smiles, molSize=(512, 512), rotate=0, kekulize=True):
    """This function takes the user input SMILES and Canonicalize it
       using the RDKit.
    Args:
            smiles (string): SMILES string given by the user.
    Returns:
            image (SVG): RDKit Structure Depiction as a SVG image.
    """
    if any(char.isspace() for char in smiles):
        smiles = smiles.replace(" ", "+")
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        mc = Chem.Mol(mol.ToBinary())
        if kekulize:
            try:
                Chem.Kekulize(mc)
            except Exception as e:
                print(e, flush=True)
                mc = Chem.Mol(mol.ToBinary())
        if not mc.GetNumConformers():
            rdDepictor.Compute2DCoords(mc)
        drawer = rdMolDraw2D.MolDraw2DSVG(molSize[0], molSize[1])
        drawer.drawOptions().rotate = rotate
        drawer.DrawMolecule(mc)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        return svg.replace("svg:", "")
    else:
        return "Error reading SMILES string, check again."
