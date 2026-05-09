# ML Kit + Retrofit + Moshi + Room — keep model/DTO classes
-keep class com.ledgr.scanner.data.** { *; }
-keepclassmembers class * { @com.squareup.moshi.Json *; }
-keep class kotlin.Metadata { *; }
-dontwarn javax.lang.model.element.Modifier
