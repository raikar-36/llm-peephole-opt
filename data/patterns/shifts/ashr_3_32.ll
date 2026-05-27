define i32 @pattern_ashr_3_32(i32 %x) {
entry:
  %result = ashr i32 %x, 3
  ret i32 %result
}
