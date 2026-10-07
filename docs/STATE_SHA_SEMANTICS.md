# State.sha Semantics — User-Approved Option C

## القرار

اعتماد Option C رسميًا:

- state.sha = مؤشر إلى commit سابق
  يحمل أحدث حالة معتمدة.
- state.sha_semantics = "parent_state_commit_pointer".
- canonical_content_sha = مؤشر إلى المحتوى
  الذي اعتُبر canonical للحالة.
- state.sha لا يُستخدم كمرجع لـmain HEAD.

## الفرق عن التعريف الأصلي

- **التعريف الأصلي (تعليمات المشروع، بند 8):**
  "sha = commit آخر تحديث للحالة"
- **التعريف الجديد (Option C):**
  "sha = مؤشر إلى commit سابق يحمل أحدث حالة معتمدة"

## سبب التغيير

التعريف الأصلي كان يخلق حلقة لا تنتهي:
كل commit يعدّل state.json يحتاج commit إضافي
لتحديث state.sha، وهذا الـcommit بدوره يحتاج
تحديث state.sha، وهكذا.

Option C يكسر الحلقة:
state.sha = commit السابق (لا الحالي).

## مثال تطبيقي (الحالة الحالية)

  a7db0153...  ← آخر commit غيّر الحالة الفعلية
       ↓
  ccb010e4...  ← commit سجّل canonical_content_sha
       ↓
  3f2a9f98...  ← commit لاحق

بعد Option C:
  state.sha = a7db0153...
  state.sha_semantics = "parent_state_commit_pointer"
  canonical_content_sha = a7db0153...

## ملاحظة: تساوي state.sha و canonical_content_sha

تساويهما في هذه الحالة **ليس قاعدة**.
حدث بالصدفة لأن a7db0153 يمثل آخر commit
فعلي للحالة قبل تسجيل المؤشر.

## التصنيف

- **النوع:** قرار حوكمة/تنفيذ من المستخدم.
- **ليس:** قاعدة من المرجع الأصلي.
- **الحالة:** APPROVED-BY-USER.
- **التاريخ:** 2026-10-08T01:32:17+02:00

## المرجعيات المتأثرة

- تعليمات المشروع، بند 8 (state.json).
- هذا التوثيق يُلغي الدلالة القديمة لـstate.sha
  ويحل محلها الدلالة الجديدة.
