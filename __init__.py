bl_info = {
	"name": "Apply Modifier to Multiuser",
	"author": "Kenetics",
	"version": (0, 1),
	"blender": (2, 80, 0),
	"location": "View3D > Operator Search > ",
	"description": "Apply modifier to objects that are multi-user",
	"warning": "",
	"wiki_url": "",
	"category": "Modelling"
}

import bpy, math
from bpy.props import EnumProperty, IntProperty, FloatVectorProperty, BoolProperty, FloatProperty, StringProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel, AddonPreferences

## Helper Functions
def are_modifiers_same(mod1, mod2):
	return all( getattr(mod1, prop, True) == getattr(mod2, prop, False) for prop in mod1.bl_rna.properties.keys() )

def are_modifiers_similar(mod1, mod2, tolerance):
	# Go through modifier properties
	for prop in mod1.bl_rna.properties.keys():
		## Properties to ignore and not compare
		if prop in {"name", "custom_profile"}:
			continue
		## Special comparisons
		# if property is float
		elif type(getattr(mod1, prop)) == type(1.0):
			# check if properties are close to each other within tolerance
			if not math.isclose(getattr(mod1, prop), getattr(mod2, prop), rel_tol=tolerance):
				return False
		
		## Default comparison
		elif getattr(mod1, prop, True) != getattr(mod2, prop, False):
			return False
	
	return True

## Operators

class AMTMU_OT_apply_modifier_to_multi_user(Operator):
	"""Applies modifier to a multi user object. Removes only the modifier that is similar, disregarding the names."""
	bl_idname = "amtmu.apply_modifier_to_multi_user"
	bl_label = "Apply Modifier to MultiUser"
	bl_options = {'REGISTER','UNDO'}
	
	selected_only : BoolProperty(name="Selected Only", default=False)
	
	modifier_index : IntProperty(name="Modifier Index", default=0)
	
	tolerance : FloatProperty(
		name="Tolerance",
		default=0.0001
	)
	
	no_modifier_mode : EnumProperty(
		items=(
			("FORCE", "Force", "Applies same mesh to other linked objects, even if they don't have the applied modifier, distorting the shape.", "", 0),
			("KEEP_SHAPE", "Keep Shape", "If other linked object doesn't have same modifier, it will keep its object data, keeping its shape.", "", 1)
		),
		name="No Modifier Mode",
		description="For linked objects which do not have same modifier as active mesh."
	)

	@classmethod
	def poll(cls, context):
		return (
			context.active_object and
			context.active_object.type == "MESH" and
			context.active_object.modifiers
		)

	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)

	def execute(self, context):
		# cache active
		active_obj = context.active_object
		active_mod = active_obj.modifiers[self.modifier_index]
		# cache other linked objs
		other_objs = []
		
		if self.selected_only:
			objs = context.selected_objects
		else:
			objs = context.scene.objects
		
		for obj in objs:
			# if this is same obj
			if obj == active_obj:
				continue
			elif obj.data == active_obj.data:
				for mod in obj.modifiers:
					if are_modifiers_similar(mod, active_mod, self.tolerance):
						## remove the modifier from other objs
						obj.modifiers.remove(mod)
						other_objs.append(obj)
						break
				else:
					# Couldnt find a matching modifier
					if self.no_modifier_mode == "FORCE":
						other_objs.append(obj)
		
		# make active object data unique
		active_obj.data = active_obj.data.copy()
		
		# apply modifier on active obj
		bpy.ops.object.modifier_apply(modifier=active_obj.modifiers[self.modifier_index].name)
		
		# rejoin linked objects
		for obj in other_objs:
			obj.data = active_obj.data
		
		return {'FINISHED'}


## Preferences
class AMTMU_addon_preferences(AddonPreferences):
	"""Addon Preferences"""
	bl_idname = __name__
	
	# Properties
	show_mini_manual : BoolProperty(
		name="Show Mini Manual",
		default=False
	)

	def draw(self, context):
		layout = self.layout
		
		# Mini Manual
		layout.prop(self, "show_mini_manual", toggle=True)
		
		if self.show_mini_manual:
			col = layout.col(align=True)
			col.label(text="Category:", icon="DOT")
			col.label(text="Text", icon="THREE_DOTS")

## Register

classes = (
	AMTMU_OT_apply_modifier_to_multi_user,
	AMTMU_addon_preferences
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

if __name__ == "__main__":
	register()
