-- =============================================================================
-- Migración de evidencias (fotos) al modelo por producto
-- Ejecutar en PostgreSQL (RDS) — esquema public
--
-- NOTA: Sin BEGIN/COMMIT para evitar "there is no transaction in progress"
--       en pgAdmin/DBeaver cuando se ejecuta línea por línea.
--       Selecciona TODO el bloque y ejecútalo de una vez (F5).
-- =============================================================================

-- 0) Verificar versión de migraciones
SELECT av.*
FROM public.alembic_version AS av;
-- Debe mostrar: 0014_pqrs_satisfaccion

-- -----------------------------------------------------------------------------
-- 1) Actualizar evidencias existentes sin producto
-- -----------------------------------------------------------------------------
WITH ranked_evidencias AS (
    SELECT
        e.id,
        e.pqrs_id,
        (ROW_NUMBER() OVER (PARTITION BY e.pqrs_id ORDER BY e.id) - 1)::int AS rn
    FROM public.evidencias AS e
    WHERE e.producto_pqrs_id IS NULL
),
ranked_productos AS (
    SELECT
        pp.id AS producto_pqrs_id,
        pp.pqrs_id,
        (ROW_NUMBER() OVER (PARTITION BY pp.pqrs_id ORDER BY pp.id) - 1)::int AS prod_rn
    FROM public.productos_pqrs AS pp
),
producto_count AS (
    SELECT
        pp.pqrs_id,
        COUNT(*)::int AS n_prod
    FROM public.productos_pqrs AS pp
    GROUP BY pp.pqrs_id
),
asignacion AS (
    SELECT
        re.id AS evidencia_id,
        rp.producto_pqrs_id,
        CASE MOD(re.rn, 2)
            WHEN 0 THEN 'NO_CONFORMIDAD'
            ELSE 'FOTO_LOTE'
        END AS tipo,
        CASE MOD(re.rn, 2)
            WHEN 0 THEN 'Por no conformidad'
            ELSE 'Foto del lote'
        END AS titulo
    FROM ranked_evidencias AS re
    INNER JOIN producto_count AS pc ON pc.pqrs_id = re.pqrs_id
    INNER JOIN ranked_productos AS rp
        ON rp.pqrs_id = re.pqrs_id
       AND rp.prod_rn = (re.rn / 2)
    WHERE (re.rn / 2) < pc.n_prod
)
UPDATE public.evidencias AS e
SET
    producto_pqrs_id = a.producto_pqrs_id,
    tipo = a.tipo,
    titulo = a.titulo
FROM asignacion AS a
WHERE e.id = a.evidencia_id;

-- -----------------------------------------------------------------------------
-- 2) PQRS 1: insertar fotos de ejemplo
-- -----------------------------------------------------------------------------
INSERT INTO public.evidencias (
    pqrs_id,
    producto_pqrs_id,
    tipo,
    titulo,
    archivo_url,
    nombre_original,
    content_type
)
SELECT
    1,
    pp.id,
    v.tipo,
    v.titulo,
    v.archivo_url,
    v.nombre_original,
    v.content_type
FROM public.productos_pqrs AS pp
CROSS JOIN (
    VALUES
        (
            'NO_CONFORMIDAD',
            'Por no conformidad',
            '/uploads/pqrs/1/productos/1/dc5980c867f84e7ab29481e1750c85f5.webp',
            'evidencia-no-conformidad.webp',
            'image/webp'
        ),
        (
            'FOTO_LOTE',
            'Foto del lote',
            '/uploads/pqrs/1/productos/1/ef3c2ba206254d589821ecf0aab77108.webp',
            'evidencia-foto-lote.webp',
            'image/webp'
        )
) AS v(tipo, titulo, archivo_url, nombre_original, content_type)
WHERE pp.pqrs_id = 1
  AND NOT EXISTS (
      SELECT 1
      FROM public.evidencias AS e
      WHERE e.pqrs_id = 1
        AND e.producto_pqrs_id = pp.id
        AND e.tipo = v.tipo
  );

-- -----------------------------------------------------------------------------
-- 3) Verificación
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*) FILTER (WHERE e.producto_pqrs_id IS NULL) AS sin_producto,
    COUNT(*) FILTER (WHERE e.producto_pqrs_id IS NOT NULL) AS con_producto
FROM public.evidencias AS e;

SELECT
    p.radicado,
    pp.id AS producto_id,
    pp.nombre_producto,
    e.tipo,
    e.titulo,
    e.archivo_url
FROM public.evidencias AS e
INNER JOIN public.pqrs AS p ON p.id = e.pqrs_id
INNER JOIN public.productos_pqrs AS pp ON pp.id = e.producto_pqrs_id
ORDER BY p.id, pp.id, e.tipo;

-- -----------------------------------------------------------------------------
-- 4) (Opcional) Borrar fotos sobrantes — ejecutar solo si lo necesitas
-- -----------------------------------------------------------------------------
-- DELETE FROM public.evidencias AS e
-- WHERE e.producto_pqrs_id IS NULL;
