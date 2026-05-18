import re
import bpy
from bpy.types import Operator, Menu
from bpy.props import StringProperty
from bpy.utils import register_class, unregister_class


def _node_label(type_name):
    t = getattr(bpy.types, type_name, None)
    if t is not None:
        label = getattr(t, 'bl_label', None)
        if label:
            return label
    name = type_name
    for prefix in ('OctaneMX', 'OctaneOutputAOVs', 'OctaneSDF', 'OctaneTexLayer',
                   'OctaneOutputAOV', 'Octane'):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', name)


def _swap_op(layout, type_name):
    op = layout.operator('opstyix.swap_octane_node_type_exec', text=_node_label(type_name))
    op.node_type = type_name


# ── Texture subcategories ──────────────────────────────────────────────────────

class OPSTYIX_MT_Swap_Texture_Image(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Texture_Image'
    bl_label  = 'Image'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneAlphaImage', 'OctaneBakingTexture', 'OctaneGreyscaleImage',
                  'OctaneRGBImage', 'OctaneTileGridImage', 'OctaneUVTiles'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Texture_Procedural(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Texture_Procedural'
    bl_label  = 'Procedural'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneCMYKHalftone', 'OctaneCellNoise', 'OctaneChainmail',
                  'OctaneChecksTexture', 'OctaneCinema4DNoise', 'OctaneCircleSpiral',
                  'OctaneColorSquares', 'OctaneDigits', 'OctaneFBMFlowNoise',
                  'OctaneFBMNoise', 'OctaneFanSpiral', 'OctaneFlakes',
                  'OctaneFractalFlowNoise', 'OctaneFractalNoise', 'OctaneGlowingCircle',
                  'OctaneGradientGenerator', 'OctaneHagelslag', 'OctaneIridescent',
                  'OctaneMandelbulb', 'OctaneMarbleTexture', 'OctaneMatrixEffect',
                  'OctaneMoireMosaic', 'OctaneNoiseTexture', 'OctanePixelFlow',
                  'OctaneProceduralEffects', 'OctaneRainBump', 'OctaneRidgedFractalTexture',
                  'OctaneRotFractal', 'OctaneSawWaveTexture', 'OctaneScratches',
                  'OctaneSineWaveFan', 'OctaneSineWaveTexture', 'OctaneSmoothVoronoiContours',
                  'OctaneSnowEffect', 'OctaneStarField', 'OctaneStripes',
                  'OctaneTilePatterns', 'OctaneTriangleWaveTexture', 'OctaneTripper',
                  'OctaneTurbulenceTexture', 'OctaneVolumeCloud', 'OctaneWavePattern',
                  'OctaneWoodgrain'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Texture_Converters(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Texture_Converters'
    bl_label  = 'Converters'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneFloat3ToColor', 'OctaneFloatToGreyscale', 'OctaneFloatsToColor',
                  'OctaneTransformToMatrix', 'OctaneVolumeToTexture'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Texture_Fields(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Texture_Fields'
    bl_label  = 'Fields'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneAngularField', 'OctanePlanarField', 'OctaneShapeField',
                  'OctaneSphericalField'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Texture_Geometric(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Texture_Geometric'
    bl_label  = 'Geometric'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneColorVertexAttribute', 'OctaneCurvatureTexture', 'OctaneDirtTexture',
                  'OctaneFalloffMap', 'OctaneGreyscaleVertexAttribute', 'OctaneInstanceColor',
                  'OctaneInstanceHighlight', 'OctaneInstanceRange', 'OctaneNormal',
                  'OctaneObjectLayerColor', 'OctanePolygonSide', 'OctanePosition',
                  'OctaneRandomColorTexture', 'OctaneRayDirection', 'OctaneRelativeDistance',
                  'OctaneSamplePosition', 'OctaneSurfaceTangentDPdu', 'OctaneSurfaceTangentDPdv',
                  'OctaneUVCoordinate', 'OctaneUVCoordinateWithTransform', 'OctaneWCoordinate',
                  'OctaneZDepth'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Texture_Mapping(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Texture_Mapping'
    bl_label  = 'Mapping'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneChaosTexture', 'OctaneTriplanarMap', 'OctaneUVWTransform'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Texture_Operators(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Texture_Operators'
    bl_label  = 'Operators'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneAddTexture', 'OctaneBinaryMathOperation', 'OctaneClampTexture',
                  'OctaneColorCorrection', 'OctaneColorKey', 'OctaneColorSpaceConversion',
                  'OctaneComparison', 'OctaneCosineMixTexture', 'OctaneGradientMap',
                  'OctaneImageAdjustment', 'OctaneInvertTexture', 'OctaneJitteredColorCorrection',
                  'OctaneMixTexture', 'OctaneMultiplyTexture', 'OctaneRandomMap',
                  'OctaneRange', 'OctaneSubtractTexture', 'OctaneUnaryMathOperation'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Texture_Utility(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Texture_Utility'
    bl_label  = 'Utility'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneCaptureToCustomAOV', 'OctaneChannelInverter', 'OctaneChannelMapper',
                  'OctaneChannelMerger', 'OctaneChannelPicker', 'OctaneDecalTexture',
                  'OctaneOutputAOVParameter', 'OctaneRaySwitch', 'OctaneSpotlight',
                  'OctaneTextureSwitch'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Texture(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Texture'
    bl_label  = 'Octane Texture'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneGaussianSpectrum', 'OctaneGreyscaleColor', 'OctaneMatrix',
                  'OctaneOSLTexture', 'OctaneRGBAColor', 'OctaneRGBColor'):
            _swap_op(L, t)
        L.separator()
        L.menu('OPSTYIX_MT_Swap_Texture_Image')
        L.menu('OPSTYIX_MT_Swap_Texture_Procedural')
        L.menu('OPSTYIX_MT_Swap_Texture_Converters')
        L.menu('OPSTYIX_MT_Swap_Texture_Fields')
        L.menu('OPSTYIX_MT_Swap_Texture_Geometric')
        L.menu('OPSTYIX_MT_Swap_Texture_Mapping')
        L.menu('OPSTYIX_MT_Swap_Texture_Operators')
        L.menu('OPSTYIX_MT_Swap_Texture_Utility')


# ── MaterialX subcategories ────────────────────────────────────────────────────

class OPSTYIX_MT_Swap_MX_Adjustment(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Adjustment'
    bl_label  = 'Adjustment'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXColorCorrect', 'OctaneMXContrast', 'OctaneMXHsvAdjust',
                  'OctaneMXHsvToRgb', 'OctaneMXLuminance', 'OctaneMXRange',
                  'OctaneMXRemap', 'OctaneMXRgbToHsv', 'OctaneMXSaturate', 'OctaneMXSmoothStep'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Application(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Application'
    bl_label  = 'Application'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXFrame', 'OctaneMXTime', 'OctaneMXUpDirection', 'OctaneMXViewDirection'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Blend(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Blend'
    bl_label  = 'Blend'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXBurn', 'OctaneMXDifference', 'OctaneMXDodge', 'OctaneMXMinus',
                  'OctaneMXOverlay', 'OctaneMXPlus', 'OctaneMXScreen'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Channels(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Channels'
    bl_label  = 'Channels'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXCombine2', 'OctaneMXCombine2Col3Float', 'OctaneMXCombine2Vec2Float',
                  'OctaneMXCombine2Vec2Vec2', 'OctaneMXCombine2Vec3Float', 'OctaneMXCombine3',
                  'OctaneMXCombine4', 'OctaneMXConvert', 'OctaneMXExtract2',
                  'OctaneMXExtract3', 'OctaneMXExtract4'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Composite(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Composite'
    bl_label  = 'Composite'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXMix', 'OctaneMXPremult', 'OctaneMXUnpremult'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Conditional(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Conditional'
    bl_label  = 'Conditional'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXAnd', 'OctaneMXIfEqual', 'OctaneMXIfEqualB',
                  'OctaneMXIfEqualBoolean', 'OctaneMXIfGreater', 'OctaneMXIfGreaterBoolean',
                  'OctaneMXIfGreaterEq', 'OctaneMXIfGreaterEqBoolean', 'OctaneMXNot',
                  'OctaneMXOr', 'OctaneMXSwitch', 'OctaneMXXor'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Geometry(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Geometry'
    bl_label  = 'Geometry'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXBiTangent', 'OctaneMXBump', 'OctaneMXFacingRatio',
                  'OctaneMXGeomColor', 'OctaneMXGeomPropValue', 'OctaneMXNormal',
                  'OctaneMXPosition', 'OctaneMXTangent', 'OctaneMXTexCoord'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Mask(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Mask'
    bl_label  = 'Mask'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXInside', 'OctaneMXOutside'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Math(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Math'
    bl_label  = 'Math'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXACos', 'OctaneMXASin', 'OctaneMXATan2', 'OctaneMXAbs',
                  'OctaneMXAdd', 'OctaneMXCeil', 'OctaneMXClamp', 'OctaneMXCos',
                  'OctaneMXDeterminant', 'OctaneMXDivide', 'OctaneMXExp', 'OctaneMXFloor',
                  'OctaneMXFract', 'OctaneMXInvert', 'OctaneMXInvertMatrix', 'OctaneMXLn',
                  'OctaneMXMax', 'OctaneMXMin', 'OctaneMXModulo', 'OctaneMXMultiply',
                  'OctaneMXPower', 'OctaneMXRound', 'OctaneMXSafePower', 'OctaneMXSign',
                  'OctaneMXSin', 'OctaneMXSqrt', 'OctaneMXSubtract', 'OctaneMXTan',
                  'OctaneMXTranspose', 'OctaneMXTriangleWave'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Merge(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Merge'
    bl_label  = 'Merge'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXDisjointover', 'OctaneMXIn', 'OctaneMXMask',
                  'OctaneMXMatte', 'OctaneMXOut', 'OctaneMXOver'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Procedural(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Procedural'
    bl_label  = 'Procedural'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXCellNoise2d', 'OctaneMXCellNoise3d', 'OctaneMXConstant',
                  'OctaneMXFractal2d', 'OctaneMXFractal3d', 'OctaneMXNoise2d',
                  'OctaneMXNoise3d', 'OctaneMXPlace2d', 'OctaneMXRamp4', 'OctaneMXRampLR',
                  'OctaneMXRampTB', 'OctaneMXRandomColor', 'OctaneMXRandomFloat',
                  'OctaneMXSplitLR', 'OctaneMXSplitTB', 'OctaneMXWorleyNoise2d',
                  'OctaneMXWorleyNoise3d'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Source(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Source'
    bl_label  = 'Source'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXHexTiledImage', 'OctaneMXHexTiledNormalMap', 'OctaneMXImage',
                  'OctaneMXLatLongImage', 'OctaneMXTiledImage', 'OctaneMXTriPlanarProjection'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MX_Vector(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MX_Vector'
    bl_label  = 'Vector'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneMXCreateMatrix', 'OctaneMXCreateMatrix3x3', 'OctaneMXCrossProduct',
                  'OctaneMXDistance', 'OctaneMXDotProduct', 'OctaneMXHeightToNormal',
                  'OctaneMXMagnitude', 'OctaneMXNormalMap', 'OctaneMXNormalize',
                  'OctaneMXReflect', 'OctaneMXRefract', 'OctaneMXRotate2d', 'OctaneMXRotate3d',
                  'OctaneMXTransformMatrix', 'OctaneMXTransformMatrix3x3',
                  'OctaneMXTransformNormal', 'OctaneMXTransformPoint', 'OctaneMXTransformVector'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MaterialX(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MaterialX'
    bl_label  = 'Octane MaterialX'
    def draw(self, context):
        L = self.layout
        L.menu('OPSTYIX_MT_Swap_MX_Adjustment')
        L.menu('OPSTYIX_MT_Swap_MX_Application')
        L.menu('OPSTYIX_MT_Swap_MX_Blend')
        L.menu('OPSTYIX_MT_Swap_MX_Channels')
        L.menu('OPSTYIX_MT_Swap_MX_Composite')
        L.menu('OPSTYIX_MT_Swap_MX_Conditional')
        L.menu('OPSTYIX_MT_Swap_MX_Geometry')
        L.menu('OPSTYIX_MT_Swap_MX_Mask')
        L.menu('OPSTYIX_MT_Swap_MX_Math')
        L.menu('OPSTYIX_MT_Swap_MX_Merge')
        L.menu('OPSTYIX_MT_Swap_MX_Procedural')
        L.menu('OPSTYIX_MT_Swap_MX_Source')
        L.menu('OPSTYIX_MT_Swap_MX_Vector')


# ── Composite Texture subcategories ───────────────────────────────────────────

class OPSTYIX_MT_Swap_CompTex_Blend(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_CompTex_Blend'
    bl_label  = 'Blend'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneTexLayerLayerGroup', 'OctaneTexLayerTexture'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_CompTex_Color(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_CompTex_Color'
    bl_label  = 'Effects - Color'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneTexLayerAdjustBrightness', 'OctaneTexLayerAdjustColorBalance',
                  'OctaneTexLayerAdjustContrast', 'OctaneTexLayerAdjustExposure',
                  'OctaneTexLayerAdjustHue', 'OctaneTexLayerAdjustLightness',
                  'OctaneTexLayerAdjustSaturation', 'OctaneTexLayerAdjustSaturationHSL',
                  'OctaneTexLayerAdjustWhiteBalance', 'OctaneTexLayerApplyCustomCurve',
                  'OctaneTexLayerApplyGammaCurve', 'OctaneTexLayerApplyGradientMap',
                  'OctaneTexLayerApplyLUT', 'OctaneTexLayerConvertToGreyscale'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_CompTex_Opacity(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_CompTex_Opacity'
    bl_label  = 'Effects - Opacity'
    def draw(self, context):
        _swap_op(self.layout, 'OctaneTexLayerMask')

class OPSTYIX_MT_Swap_CompTex_Operators(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_CompTex_Operators'
    bl_label  = 'Operators'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneTexLayerChannelMixer', 'OctaneTexLayerClamp',
                  'OctaneTexLayerComparison', 'OctaneTexLayerMapRange',
                  'OctaneTexLayerMathBinary', 'OctaneTexLayerMathUnary',
                  'OctaneTexLayerThreshold'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_CompositeTexture(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_CompositeTexture'
    bl_label  = 'Composite Texture'
    def draw(self, context):
        L = self.layout
        _swap_op(L, 'OctaneCompositeTexture')
        L.separator()
        L.menu('OPSTYIX_MT_Swap_CompTex_Blend')
        L.menu('OPSTYIX_MT_Swap_CompTex_Color')
        L.menu('OPSTYIX_MT_Swap_CompTex_Opacity')
        L.menu('OPSTYIX_MT_Swap_CompTex_Operators')
        L.separator()
        _swap_op(L, 'OctaneTextureLayerSwitch')


# ── Vectron subcategories ──────────────────────────────────────────────────────

class OPSTYIX_MT_Swap_Vectron_Combine(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Vectron_Combine'
    bl_label  = 'Combine Operators'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneSDFAvoid', 'OctaneSDFInk', 'OctaneSDFIntersect', 'OctaneSDFPull',
                  'OctaneSDFPush', 'OctaneSDFRepel', 'OctaneSDFSubtract', 'OctaneSDFUnion'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Vectron_Repeat(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Vectron_Repeat'
    bl_label  = 'Repeat Operators'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneSDFCircularArray', 'OctaneSDFLinearArray', 'OctaneSDFMirror'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Vectron_Shape(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Vectron_Shape'
    bl_label  = 'Shape Operators'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneSDFClip', 'OctaneSDFDomainTransform', 'OctaneSDFOffset',
                  'OctaneSDFVectronDisplacement'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Vectron(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Vectron'
    bl_label  = 'Octane Vectron'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneSDFBox', 'OctaneSDFCapsule', 'OctaneSDFCone', 'OctaneSDFCylinder',
                  'OctaneSDFPrism', 'OctaneSDFSphere', 'OctaneSDFTorus', 'OctaneVectron'):
            _swap_op(L, t)
        L.separator()
        L.menu('OPSTYIX_MT_Swap_Vectron_Combine')
        L.menu('OPSTYIX_MT_Swap_Vectron_Repeat')
        L.menu('OPSTYIX_MT_Swap_Vectron_Shape')


# ── Flat category menus ────────────────────────────────────────────────────────

class OPSTYIX_MT_Swap_Material(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Material'
    bl_label  = 'Octane Material'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneClippingMaterial', 'OctaneCompositeMaterial', 'OctaneDiffuseMaterial',
                  'OctaneGlossyMaterial', 'OctaneHairMaterial', 'OctaneLayeredMaterial',
                  'OctaneMetallicMaterial', 'OctaneMixMaterial', 'OctaneNullMaterial',
                  'OctaneOpenPBRSurfaceMaterial', 'OctanePortalMaterial',
                  'OctaneShadowCatcherMaterial', 'OctaneSpecularMaterial',
                  'OctaneStandardSurfaceMaterial', 'OctaneToonMaterial',
                  'OctaneToonRamp', 'OctaneUniversalMaterial'):
            _swap_op(L, t)
        L.separator()
        _swap_op(L, 'OctaneMaterialSwitch')
        _swap_op(L, 'OctaneToonRampSwitch')

class OPSTYIX_MT_Swap_Displacement(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Displacement'
    bl_label  = 'Octane Displacement'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneTextureDisplacement', 'OctaneVertexDisplacement',
                  'OctaneVertexDisplacementMixer'):
            _swap_op(L, t)
        L.separator()
        _swap_op(L, 'OctaneDisplacementSwitch')

class OPSTYIX_MT_Swap_Projection(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Projection'
    bl_label  = 'Octane Projection'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneBox', 'OctaneColorToUVW', 'OctaneCylindrical', 'OctaneDistortedMeshUV',
                  'OctaneDistortedUVW', 'OctaneInstancePosition', 'OctaneMatCap',
                  'OctaneMeshUVProjection', 'OctaneOSLDelayedUV', 'OctaneOSLProjection',
                  'OctanePerspective', 'OctaneSamplePosToUV', 'OctaneSpherical',
                  'OctaneTriplanar', 'OctaneXYZToUVW'):
            _swap_op(L, t)
        L.separator()
        _swap_op(L, 'OctaneCameraProjection')
        _swap_op(L, 'OctaneProjectionSwitch')

class OPSTYIX_MT_Swap_Transform(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Transform'
    bl_label  = 'Octane Transform'
    def draw(self, context):
        L = self.layout
        for t in ('Octane2DTransformation', 'Octane3DTransformation',
                  'OctaneConverterLookAtTransform', 'OctaneRotation', 'OctaneScale',
                  'OctaneTransformValue', 'OctaneUVTilingAndOffset'):
            _swap_op(L, t)
        L.separator()
        _swap_op(L, 'OctaneTransformSwitch')
        _swap_op(L, 'OctaneCameraTransformation')

class OPSTYIX_MT_Swap_Medium(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Medium'
    bl_label  = 'Octane Medium'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneAbsorption', 'OctaneRandomWalk', 'OctaneScattering', 'OctaneSchlick',
                  'OctaneStandardVolumeMedium', 'OctaneVolumeGradient', 'OctaneVolumeMedium'):
            _swap_op(L, t)
        L.separator()
        _swap_op(L, 'OctaneMediumSwitch')
        _swap_op(L, 'OctanePhaseFunctionSwitch')
        _swap_op(L, 'OctaneVolumeRampSwitch')

class OPSTYIX_MT_Swap_Emission(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Emission'
    bl_label  = 'Octane Emission'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneBlackBodyEmission', 'OctaneTextureEmission', 'OctaneEmissionSwitch'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Environment(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Environment'
    bl_label  = 'Octane Environment'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneDaylightEnvironment', 'OctanePlanetaryEnvironment',
                  'OctaneTextureEnvironment', 'OctaneEnvironmentSwitch'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Geometry(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Geometry'
    bl_label  = 'Octane Geometry'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneDecal', 'OctaneGaussianSplat', 'OctaneGeometricPrimitive',
                  'OctaneMesh', 'OctaneMeshVolume', 'OctaneMeshVolumeSDF',
                  'OctanePlane', 'OctaneUnitVolume', 'OctaneVolume', 'OctaneVolumeSDF'):
            _swap_op(L, t)
        L.separator()
        L.label(text="Scatter tools")
        for t in ('OctaneScatter', 'OctaneScatterInVolume', 'OctaneScatterOnSurface'):
            _swap_op(L, t)
        L.separator()
        for t in ('OctaneGeometryExporter', 'OctaneGeometryGroup', 'OctaneGeometrySwitch',
                  'OctaneJoint', 'OctaneMaterialMap', 'OctaneObjectLayer',
                  'OctaneObjectLayerMap', 'OctaneObjectLayerSwitch', 'OctanePlacement'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_MaterialLayer(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_MaterialLayer'
    bl_label  = 'Octane Material Layer'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneDiffuseLayer', 'OctaneMaterialLayerGroup', 'OctaneMetallicLayer',
                  'OctaneSheenLayer', 'OctaneSpecularLayer'):
            _swap_op(L, t)
        L.separator()
        _swap_op(L, 'OctaneMaterialLayerSwitch')

class OPSTYIX_MT_Swap_Values(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Values'
    bl_label  = 'Octane Values'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneBoolValue', 'OctaneIntValue', 'OctaneFloatValue',
                  'OctaneRGBColorToFloat3', 'OctaneStringValue',
                  'OctaneLightIDBitValue', 'OctaneSunDirection'):
            _swap_op(L, t)
        L.separator()
        L.label(text="Converters")
        for t in ('OctaneConverterFloatToInt', 'OctaneConverterIntToFloat'):
            _swap_op(L, t)
        L.separator()
        L.label(text="Operators")
        for t in ('OctaneOperatorBinaryMathOperation', 'OctaneOperatorBooleanLogicOperator',
                  'OctaneOperatorFloatRelationalOperator', 'OctaneOperatorIntRelationalOperator',
                  'OctaneOperatorRange', 'OctaneOperatorRotate', 'OctaneOperatorUnaryMathOperation'):
            _swap_op(L, t)
        L.separator()
        L.label(text="Utility")
        for t in ('OctaneBitMaskSwitch', 'OctaneBoolSwitch', 'OctaneFloatSwitch',
                  'OctaneFrameIndex', 'OctaneIntSwitch', 'OctaneStringSwitch', 'OctaneTime',
                  'OctaneUtilityFloatComponentPicker', 'OctaneUtilityFloatIf',
                  'OctaneUtilityFloatMerger', 'OctaneUtilityIntComponentPicker',
                  'OctaneUtilityIntIf', 'OctaneUtilityIntMerger'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_CyclesWrappers(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_CyclesWrappers'
    bl_label  = 'Cycles Texture Wrappers'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneCyclesMixColorNodeWrapper', 'OctaneCyclesMixFloatNodeWrapper',
                  'OctaneCyclesMixFloat3NodeWrapper', 'OctaneCyclesNodeMathNodeWrapper',
                  'OctaneCyclesNodeVectorMathNodeWrapper'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_AdvancedTools(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_AdvancedTools'
    bl_label  = 'Octane Advanced Tools'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneCameraData', 'OctaneObjectData', 'OctaneScriptGraph', 'OctaneProxy'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_RoundEdge(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_RoundEdge'
    bl_label  = 'Octane Round Edge'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneRoundEdges', 'OctaneRoundEdgesSwitch'):
            _swap_op(L, t)

class OPSTYIX_MT_Swap_Camera(Menu):
    bl_idname = 'OPSTYIX_MT_Swap_Camera'
    bl_label  = 'Octane Camera'
    def draw(self, context):
        L = self.layout
        for t in ('OctaneOSLCamera', 'OctaneOSLBakingCamera'):
            _swap_op(L, t)


# ── Top-level menu ─────────────────────────────────────────────────────────────

class OPSTYIX_MT_SwapOctaneNodeType(Menu):
    bl_idname = 'OPSTYIX_MT_SwapOctaneNodeType'
    bl_label  = 'Swap Octane Node Type'
    def draw(self, context):
        L = self.layout
        L.menu('OPSTYIX_MT_Swap_Material')
        L.menu('OPSTYIX_MT_Swap_Texture')
        L.menu('OPSTYIX_MT_Swap_Displacement')
        L.menu('OPSTYIX_MT_Swap_Projection')
        L.menu('OPSTYIX_MT_Swap_Transform')
        L.menu('OPSTYIX_MT_Swap_Medium')
        L.menu('OPSTYIX_MT_Swap_Emission')
        L.menu('OPSTYIX_MT_Swap_Environment')
        L.menu('OPSTYIX_MT_Swap_Geometry')
        L.menu('OPSTYIX_MT_Swap_MaterialLayer')
        L.menu('OPSTYIX_MT_Swap_Values')
        L.menu('OPSTYIX_MT_Swap_CyclesWrappers')
        L.menu('OPSTYIX_MT_Swap_CompositeTexture')
        L.menu('OPSTYIX_MT_Swap_MaterialX')
        L.menu('OPSTYIX_MT_Swap_Vectron')
        L.menu('OPSTYIX_MT_Swap_AdvancedTools')
        L.menu('OPSTYIX_MT_Swap_RoundEdge')
        L.menu('OPSTYIX_MT_Swap_Camera')


# ── Operators ──────────────────────────────────────────────────────────────────

class OPSTYIX_OT_SwapOctaneNodeType(Operator):
    bl_idname      = 'opstyix.swap_octane_node_type'
    bl_label       = 'Swap Octane Node Type'
    bl_description = 'Replace the active Octane node with a different Octane node type, preserving connections'
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.area is None or context.area.type != 'NODE_EDITOR':
            return False
        node = context.active_node
        return node is not None and node.bl_idname.startswith('Octane')

    def invoke(self, context, event):
        bpy.ops.wm.call_menu(name='OPSTYIX_MT_SwapOctaneNodeType')
        return {'FINISHED'}

    def execute(self, context):
        return {'FINISHED'}


class OPSTYIX_OT_SwapOctaneNodeTypeExec(Operator):
    bl_idname  = 'opstyix.swap_octane_node_type_exec'
    bl_label   = 'Swap Octane Node Type'
    bl_options = {'REGISTER', 'UNDO'}

    node_type: StringProperty()

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        if node_tree is None:
            return {'CANCELLED'}

        old_node = context.active_node
        if old_node is None:
            return {'CANCELLED'}

        in_links  = [(l.from_socket, l.to_socket.name) for l in node_tree.links if l.to_node   == old_node]
        out_links = [(l.from_socket.name, l.to_socket) for l in node_tree.links if l.from_node == old_node]
        location  = old_node.location.copy()
        label     = old_node.label

        node_tree.nodes.remove(old_node)

        try:
            new_node = node_tree.nodes.new(type=self.node_type)
        except Exception as e:
            self.report({'ERROR'}, f"Could not create node: {e}")
            return {'CANCELLED'}

        new_node.location = location
        if label:
            new_node.label = label

        for from_socket, to_name in in_links:
            target = new_node.inputs.get(to_name)
            if target is not None:
                try:
                    node_tree.links.new(target, from_socket)
                except Exception:
                    pass

        for from_name, to_socket in out_links:
            source = new_node.outputs.get(from_name)
            if source is not None:
                try:
                    node_tree.links.new(source, to_socket)
                except Exception:
                    pass

        return {'FINISHED'}


# ── Registration ───────────────────────────────────────────────────────────────

CLASSES = [
    OPSTYIX_MT_Swap_Texture_Image,
    OPSTYIX_MT_Swap_Texture_Procedural,
    OPSTYIX_MT_Swap_Texture_Converters,
    OPSTYIX_MT_Swap_Texture_Fields,
    OPSTYIX_MT_Swap_Texture_Geometric,
    OPSTYIX_MT_Swap_Texture_Mapping,
    OPSTYIX_MT_Swap_Texture_Operators,
    OPSTYIX_MT_Swap_Texture_Utility,
    OPSTYIX_MT_Swap_Texture,
    OPSTYIX_MT_Swap_MX_Adjustment,
    OPSTYIX_MT_Swap_MX_Application,
    OPSTYIX_MT_Swap_MX_Blend,
    OPSTYIX_MT_Swap_MX_Channels,
    OPSTYIX_MT_Swap_MX_Composite,
    OPSTYIX_MT_Swap_MX_Conditional,
    OPSTYIX_MT_Swap_MX_Geometry,
    OPSTYIX_MT_Swap_MX_Mask,
    OPSTYIX_MT_Swap_MX_Math,
    OPSTYIX_MT_Swap_MX_Merge,
    OPSTYIX_MT_Swap_MX_Procedural,
    OPSTYIX_MT_Swap_MX_Source,
    OPSTYIX_MT_Swap_MX_Vector,
    OPSTYIX_MT_Swap_MaterialX,
    OPSTYIX_MT_Swap_CompTex_Blend,
    OPSTYIX_MT_Swap_CompTex_Color,
    OPSTYIX_MT_Swap_CompTex_Opacity,
    OPSTYIX_MT_Swap_CompTex_Operators,
    OPSTYIX_MT_Swap_CompositeTexture,
    OPSTYIX_MT_Swap_Vectron_Combine,
    OPSTYIX_MT_Swap_Vectron_Repeat,
    OPSTYIX_MT_Swap_Vectron_Shape,
    OPSTYIX_MT_Swap_Vectron,
    OPSTYIX_MT_Swap_Material,
    OPSTYIX_MT_Swap_Displacement,
    OPSTYIX_MT_Swap_Projection,
    OPSTYIX_MT_Swap_Transform,
    OPSTYIX_MT_Swap_Medium,
    OPSTYIX_MT_Swap_Emission,
    OPSTYIX_MT_Swap_Environment,
    OPSTYIX_MT_Swap_Geometry,
    OPSTYIX_MT_Swap_MaterialLayer,
    OPSTYIX_MT_Swap_Values,
    OPSTYIX_MT_Swap_CyclesWrappers,
    OPSTYIX_MT_Swap_AdvancedTools,
    OPSTYIX_MT_Swap_RoundEdge,
    OPSTYIX_MT_Swap_Camera,
    OPSTYIX_MT_SwapOctaneNodeType,
    OPSTYIX_OT_SwapOctaneNodeType,
    OPSTYIX_OT_SwapOctaneNodeTypeExec,
]

_keymaps = []


def register():
    for cls in CLASSES:
        register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km  = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new(
            'opstyix.swap_octane_node_type', type='S', value='PRESS', shift=True
        )
        _keymaps.append((km, kmi))


def unregister():
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
    for cls in reversed(CLASSES):
        unregister_class(cls)


print("octane_swap_node_type.py loaded")
