#include <malloc/malloc.h>
#include <stdio.h>
#include <errno.h>

void *(*system_malloc)(malloc_zone_t *zone, size_t size);
void (*system_free)(malloc_zone_t *zone, void *ptr);

#define KEEP_SIZE 4096
#define KEEP_NUM 100
static void* keep_list[KEEP_NUM];
static void** tail;


void *mymalloc(malloc_zone_t *zone, size_t size)
{
  if (size >= KEEP_SIZE) { // big?
    if (tail > keep_list) { // available?
      void **entry;
      for (entry = tail - 1; entry >= keep_list; entry--) {
        if (zone->size(zone, *entry) >= size) {
          void *retval = *entry;
          tail--;
          *entry = *tail;
          //fprintf(stderr, "fulfill %d w/ %d, %d on list\n", size, zone->size(zone, *entry), keep_list - tail);
          return retval;
        }
      }
    }
  }
        
  //  fprintf(stderr, "malloc %d\n", size);
  return system_malloc(zone, size);
}

void myfree(malloc_zone_t *zone, void *ptr)
{
  size_t sz = zone->size(zone, ptr);
  if (sz >= KEEP_SIZE) { // big?
    if ((tail - keep_list) < KEEP_NUM) { // space available?
      *tail = ptr;
      tail++;
      //fprintf(stderr, "kept %d, %d on list\n", sz, keep_list - tail);
      return;
    }
  }
  //  fprintf(stderr, "free %d\n", sz);
  system_free(zone, ptr);
}

void setup()
{
  malloc_zone_t * zone = malloc_default_zone();
 
  tail = keep_list;
  system_malloc = zone->malloc;
  zone->malloc = mymalloc;
  system_free = zone->free;
  zone->free = myfree;
}

void teardown()
{
  malloc_zone_t * zone = malloc_default_zone();

  while (tail > keep_list) {
    tail--;
    system_free(zone, *tail);
  }

  zone->malloc = system_malloc;
  zone->free = system_free;
}
